import streamlit as st
import os
import time
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env BEFORE accessing os.environ
load_dotenv()

from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import init_db
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from services.persistence.exercise_repository import get_users_exercises
from groq import Groq
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio
from streamlit.runtime.secrets import StreamlitSecretNotFoundError

def get_groq_api_key():
    for env_key in ("GROQ_API_KEY", "GROK_API_KEY"):
        value = os.environ.get(env_key, "")
        if value:
            return value.strip().strip('"').strip("'")

    if hasattr(st, "secrets"):
        try:
            for secret_key in ("GROQ_API_KEY", "GROK_API_KEY"):
                value = st.secrets.get(secret_key)
                if value:
                    return str(value).strip().strip('"').strip("'")
        except StreamlitSecretNotFoundError:
            pass

    return ""


def _get_config_value(*keys):
    for key in keys:
        value = os.environ.get(key, "")
        if value:
            return value.strip().strip('"').strip("'")

    if hasattr(st, "secrets"):
        try:
            for key in keys:
                value = st.secrets.get(key)
                if value:
                    return str(value).strip().strip('"').strip("'")
        except StreamlitSecretNotFoundError:
            pass

    return ""


def get_webrtc_rtc_configuration():
    twilio_sid = _get_config_value("TWILIO_ACCOUNT_SID")
    twilio_token = _get_config_value("TWILIO_AUTH_TOKEN")

    if twilio_sid and twilio_token:
        try:
            from twilio.rest import Client
            client = Client(twilio_sid, twilio_token)
            token = client.tokens.create()
            return {"iceServers": token.ice_servers}
        except Exception as e:
            st.error(f"Failed to fetch Twilio ICE servers: {e}")

    ice_servers = [
        {"urls": ["stun:stun.l.google.com:19302"]},
    ]

    turn_url = _get_config_value("TURN_SERVER_URL")
    turn_username = _get_config_value("TURN_USERNAME")
    turn_credential = _get_config_value("TURN_CREDENTIAL", "TURN_PASSWORD")

    if turn_url:
        turn_server = {"urls": [turn_url]}

        if turn_username:
            turn_server["username"] = turn_username

        if turn_credential:
            turn_server["credential"] = turn_credential

        ice_servers.insert(0, turn_server)

    return {"iceServers": ice_servers}


def main():
    st.set_page_config(
        page_icon="🏋️‍♀️",
        page_title="AI Real-time GYM Coach",
        initial_sidebar_state="expanded",
        layout="centered"
    )

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")

    init_db()

    if not render_login_wall():
        return 

    initial_session_defaults()

    if "voice_pipeline" not in st.session_state:
        api_key = get_groq_api_key()

        st.session_state._api_key_present = bool(api_key)
        st.session_state._api_key_len = len(api_key)
        st.session_state._voice_pipeline_init_error = None

        try:
            if not api_key:
                raise ValueError("GROQ_API_KEY is empty — check your .env file and ensure load_dotenv() worked")

            groq_client = Groq(api_key=api_key)
            llm_coach = LLMCoach(groq_client)
            tts = TextToSpeech()
            st.session_state.voice_pipeline = VoicePipeline(llm_coach, tts)
            print("[main] voice_pipeline initialized OK")
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            print(f"[main] voice_pipeline init FAILED: {err}")
            st.session_state.voice_pipeline = None
            st.session_state._voice_pipeline_init_error = err

    workout_started = st.session_state.get("workout_started", False)
    
    with st.sidebar:
        st.title("🏋️‍♂️ Apna AI Coach")

        if st.session_state.username:
            st.caption(f"👤 Login as {st.session_state.username}")

        st.divider()

        st.subheader("Workout Plan")

        if not workout_started:
            plan_exercise = st.selectbox("Exercise", options=EXERCISE_OPTIONS, key="plan_exercise")

            plan_sets = st.number_input("Sets", min_value=0, max_value=50, key="plan_sets", step=1)

            plan_reps = st.number_input("Reps per Set", min_value=0, max_value=50, key="plan_reps", step=1)

            st.markdown("")

            start_session_button = st.button("Start Workout", width="stretch", key="start_session_button")

            if start_session_button:
                st.session_state.exercise_type = plan_exercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.reps = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed = 0

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        exercise=plan_exercise,
                        metrics={}
                    )
                    
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.session_state.last_notified_sets_completed = 0
                st.session_state.last_notified_workout_complete = False
                st.rerun()
        else:
            exercise = st.session_state.get("exercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")

            st.info(f"**{exercise}** -- {sets} Sets / {reps} Reps")

            end_session_button = st.button("End Workout", key="end_session_button", width="stretch")

            if end_session_button:
                st.session_state.workout_started = False
                
                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_completed",
                        exercise=exercise,
                        metrics={}
                    )
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.rerun()

        # ——— AI Coach Status Debug Panel ———
        st.divider()
        st.subheader("🤖 AI Coach Status")

        vp = st.session_state.get("voice_pipeline")
        api_ok = st.session_state.get("_api_key_present", False)
        init_err = st.session_state.get("_voice_pipeline_init_error")

        if vp is None:
            if init_err:
                st.error(f"❌ Init failed:\n`{init_err}`")
            else:
                st.error("❌ AI Coach not initialized")
            st.caption(f"GROQ_API_KEY present: {api_ok} (len={st.session_state.get('_api_key_len', 0)})")
        else:
            st.success("✅ AI Coach initialized")
            llm = vp.llm
            if hasattr(llm, "last_error") and llm.last_error:
                st.warning(f"⚠️ Last API error:\n`{llm.last_error}`")
            else:
                st.caption("No recent API errors")

        if workout_started:
            st.divider()

            exercise = st.session_state.get("exercise_type")
            total_reps = st.session_state.get("reps")
            current_set_reps = st.session_state.get("current_set_reps")
            reps_per_set = st.session_state.get("reps_per_set")
            sets_completed = st.session_state.get("sets_completed")
            target_sets = st.session_state.get("target_sets")

            st.subheader("Progress")

            st.metric("Total Reps", f"{total_reps}")
            st.metric("Current Set Reps", f"{current_set_reps} / {reps_per_set}")
            st.metric("Sets Completed", f"{sets_completed} / {target_sets}")

            st.divider()

            if exercise == "Squats":
                st.subheader("Squat Metrics")
                st.metric("Knee Angle", f"{st.session_state.knee_angle}°")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Depth Status", st.session_state.depth_status)

            elif exercise == "Push-ups":
                st.subheader("Push-up Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Hip Position", st.session_state.hip_status)

            elif exercise == "Biceps Curls (Dumbbell)":
                st.subheader("Curl Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Shoulder Stability", st.session_state.shoulder_status)
                st.metric("Swing Detection", st.session_state.swing_status)

            elif exercise == "Shoulder Press":
                st.subheader("Shoulder Press Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Arm Extension", st.session_state.extension_status)
                st.metric("Back Arch", st.session_state.back_arch_status)

            elif exercise == "Lunges":
                st.subheader("Lunge Metrics")
                st.metric("Front Knee Angle", f"{st.session_state.front_knee_angle}°")
                st.metric("Torso Angle", f"{st.session_state.torso_angle}°")
                st.metric("Balance Status", st.session_state.balance_status)

    st.title("AI Real-time GYM Coach")
    st.markdown("#### Real-time pose detection with proactive AI voice coaching")
 
    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)

    if st.session_state.get("coach_feedback"):
        st.markdown("")
        st.success(f"🤖 **Coach:** {st.session_state.coach_feedback}")

    if not workout_started:
        st.markdown(
            """
            <div style="
                border: 10px dashed #444;
                border-radius: 0px;
                padding: 48px 32px;
                text-align: center;
                color: #888;
                margin-top: 32px;
                margin-bottom: 32px;
            ">
                <h2 style="color:#ccc; margin-bottom:8px;">👈 Set your workout plan</h2>
                <p style="font-size:1.05rem;">
                    Choose your exercise, sets and reps in the sidebar,<br>
                    then click <strong>Start Workout</strong> to activate the camera and AI coach.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        context = webrtc_streamer(
            key="exercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration=get_webrtc_rtc_configuration(),
            media_stream_constraints={
                "video": True,
                "audio": False
            },
            async_processing=True
        )

        sync_metrics_update(context)

        if context.state.playing:
            time.sleep(0.25)
            st.rerun()

        inject_webrtc_styles()

    st.divider()

    st.markdown("#### Workout History")

    user_id = st.session_state.get("user_id", 0)

    if isinstance(user_id, int):
        history_rows = get_users_exercises(user_id)

        arr = [
            {
                "Exercise": row['exercise_name'],
                "Reps": row['reps'],
                "Sets": row['sets'],
                "Time (sec)": row['time'],
                "Date": row['created_at']
            }
            for row in history_rows
        ]

        df = pd.DataFrame(arr)

        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            agg_df = df.groupby(["Exercise", "Date"]).agg({
                "Reps": 'sum',
                "Sets": "sum",
                "Time (sec)": "sum"
            }).reset_index()
            agg_df.index += 1
            st.table(agg_df, border="horizontal")
        else:
            st.info("No workout history found.")


if __name__ == "__main__":
    main()
    