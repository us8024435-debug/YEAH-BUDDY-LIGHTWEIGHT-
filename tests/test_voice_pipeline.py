import pytest
from unittest.mock import Mock, patch
from services.coaching.voice_pipeline import VoicePipeline

@pytest.fixture
def mock_llm():
    llm = Mock()
    llm.give_feedback.return_value = "Good job!"
    return llm

@pytest.fixture
def mock_tts():
    tts = Mock()
    tts.speak.return_value = b"audio_bytes"
    return tts

@pytest.fixture
def pipeline(mock_llm, mock_tts):
    return VoicePipeline(mock_llm, mock_tts)

@patch("services.coaching.voice_pipeline.time.time")
def test_process_event_major_issue_no_form_issue(mock_time, pipeline, mock_llm, mock_tts):
    mock_time.return_value = 100

    # "workout_started" is a major event. Even without form issues, it should trigger speech.
    result = pipeline.process_event("workout_started", "Squats", {})

    assert result == (b"audio_bytes", "Good job!")
    mock_llm.give_feedback.assert_called_once_with("workout_started", None)
    mock_tts.speak.assert_called_once_with("Good job!")
    assert pipeline.last_spoken_at == 100

@patch("services.coaching.voice_pipeline.time.time")
def test_process_event_minor_issue_no_form_issue(mock_time, pipeline, mock_llm, mock_tts):
    mock_time.return_value = 100

    # Not a major event, no form issue. Should return None.
    result = pipeline.process_event("rep_completed", "Squats", {})

    assert result is None
    mock_llm.give_feedback.assert_not_called()
    mock_tts.speak.assert_not_called()

@patch("services.coaching.voice_pipeline.time.time")
def test_process_event_minor_issue_with_form_issue_rate_limited(mock_time, pipeline, mock_llm, mock_tts):
    # Setup initial state
    pipeline.last_spoken_at = 100
    mock_time.return_value = 104  # 4 seconds later (less than 5)

    # Form issue present (explicit issue via metrics)
    metrics = {"depth_status": "TOO HIGH"}
    result = pipeline.process_event("rep_completed", "Squats", metrics)

    # Rate limited, should return None
    assert result is None
    mock_llm.give_feedback.assert_not_called()
    mock_tts.speak.assert_not_called()

@patch("services.coaching.voice_pipeline.time.time")
def test_process_event_minor_issue_with_form_issue_not_rate_limited(mock_time, pipeline, mock_llm, mock_tts):
    # Setup initial state
    pipeline.last_spoken_at = 100
    mock_time.return_value = 105  # 5 seconds later (exactly 5, or more, is allowed since the check is `now - last < 5`)

    # Form issue present
    metrics = {"depth_status": "TOO HIGH"}
    result = pipeline.process_event("rep_completed", "Squats", metrics)

    # Should trigger speech
    assert result == (b"audio_bytes", "Good job!")
    mock_llm.give_feedback.assert_called_once_with("rep_completed", "The user's squat is not deep enough — knees are not bending sufficiently.")
    mock_tts.speak.assert_called_once_with("Good job!")
    assert pipeline.last_spoken_at == 105

def test_find_form_issue(pipeline):
    # Test a few conditions from _find_form_issue just to be thorough
    assert pipeline._find_form_issue("Squats", {"depth_status": "TOO HIGH"}) == "The user's squat is not deep enough — knees are not bending sufficiently."
    assert pipeline._find_form_issue("Push-ups", {"hip_status": "SAGGING"}) == "The user's hips are sagging down during the push-up."
    assert pipeline._find_form_issue("Lunges", {"balance_status": "OFF BALANCE"}) == "The user is losing balance during the lunge — feet should be hip-width apart."
    assert pipeline._find_form_issue("Unknown", {}) is None
