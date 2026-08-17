from services.config.workout_config import PROMPT


class LLMCoach:
    def __init__(self, groq_client):
        self.client = groq_client
        self.history = []
        self.system_prompt = PROMPT

    def give_feedback(self, event, issue):
        prompt = f"Event: {event}"

        if issue:
            prompt += f" Form Issue: {issue}"

        user_msg = {"role": "user", "content": prompt}

        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history[-10:],
            user_msg
        ]

        try:
            print(f"[LLMCoach] Calling Groq API — event={event} | has_issue={bool(issue)}")
            response = self.client.chat.completions.create(
                model="qwen/qwen3.6-27b",
                messages=messages,
                temperature=0.4,
            )

            text = response.choices[0].message.content.strip()
            self.history.append(user_msg)
            self.history.append({"role": "assistant", "content": text})
            self.last_error = None
            print(f"[LLMCoach] OK — response: {text[:80]}")

            return text
        except Exception as e:
            err_msg = f"{type(e).__name__}: {e}"
            self.last_error = err_msg
            print(f"[LLMCoach] API FAILED: {err_msg}")
            fallback = {
                "workout_started": "Let's go! Focus on form and start strong!",
                "set_completed": "Great set! Keep that energy up!",
                "workout_completed": "Amazing work! You crushed it today!",
                "no_pose_detected": "Please step into full view of the camera.",
                "ongoing_form_check": "Looking good! Keep your core tight!",
            }
            return fallback.get(event, "Keep going, you've got this!")
    