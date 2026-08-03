import pytest
from services.coaching.voice_pipeline import VoicePipeline

@pytest.fixture
def pipeline():
    # llm and tts are not needed for _find_form_issue
    return VoicePipeline(llm=None, tts=None)

def test_explicit_issue(pipeline):
    metrics = {"issue": "Test issue"}
    assert pipeline._find_form_issue("Squats", metrics) == "Test issue"

def test_squats_too_high(pipeline):
    metrics = {"depth_status": "TOO HIGH"}
    expected = "The user's squat is not deep enough — knees are not bending sufficiently."
    assert pipeline._find_form_issue("Squats", metrics) == expected

def test_squats_leaning_forward(pipeline):
    metrics = {"back_angle": 129}
    expected = "The user is leaning too far forward during the squat."
    assert pipeline._find_form_issue("Squats", metrics) == expected

def test_squats_no_issue(pipeline):
    metrics = {"depth_status": "GOOD", "back_angle": 140}
    assert pipeline._find_form_issue("Squats", metrics) is None

def test_pushups_poor_alignment(pipeline):
    metrics = {"body_alignment": "Poor Form"}
    expected = "The user's body is not straight during the push-up."
    assert pipeline._find_form_issue("Push-ups", metrics) == expected

def test_pushups_sagging_hips(pipeline):
    metrics = {"hip_status": "SAGGING"}
    expected = "The user's hips are sagging down during the push-up."
    assert pipeline._find_form_issue("Push-ups", metrics) == expected

def test_pushups_piked_hips(pipeline):
    metrics = {"hip_status": "PIKED UP"}
    expected = "The user's hips are too high — lower them to form a straight line."
    assert pipeline._find_form_issue("Push-ups", metrics) == expected

def test_pushups_no_issue(pipeline):
    metrics = {"body_alignment": "Good", "hip_status": "GOOD"}
    assert pipeline._find_form_issue("Push-ups", metrics) is None

def test_biceps_curls_swinging(pipeline):
    metrics = {"swing_status": "SWINGING"}
    expected = "The user is swinging their torso during the curl — keep the body still."
    assert pipeline._find_form_issue("Biceps Curls (Dumbbell)", metrics) == expected

def test_biceps_curls_elbow_drifting(pipeline):
    metrics = {"shoulder_status": "ELBOW DRIFTING"}
    expected = "The user's elbow is drifting away from their side during the curl."
    assert pipeline._find_form_issue("Biceps Curls (Dumbbell)", metrics) == expected

def test_biceps_curls_no_issue(pipeline):
    metrics = {"swing_status": "GOOD", "shoulder_status": "GOOD"}
    assert pipeline._find_form_issue("Biceps Curls (Dumbbell)", metrics) is None

def test_shoulder_press_excessive_arch(pipeline):
    metrics = {"back_arch_status": "Excessive Arch"}
    expected = "The user is arching their lower back excessively during the press."
    assert pipeline._find_form_issue("Shoulder Press", metrics) == expected

def test_shoulder_press_slight_arch(pipeline):
    metrics = {"back_arch_status": "Slight Arch"}
    expected = "Slight back arch detected — encourage the user to brace their core."
    assert pipeline._find_form_issue("Shoulder Press", metrics) == expected

def test_shoulder_press_no_issue(pipeline):
    metrics = {"back_arch_status": "GOOD"}
    assert pipeline._find_form_issue("Shoulder Press", metrics) is None

def test_lunges_off_balance(pipeline):
    metrics = {"balance_status": "OFF BALANCE"}
    expected = "The user is losing balance during the lunge — feet should be hip-width apart."
    assert pipeline._find_form_issue("Lunges", metrics) == expected

def test_lunges_no_issue(pipeline):
    metrics = {"balance_status": "GOOD"}
    assert pipeline._find_form_issue("Lunges", metrics) is None

def test_unknown_exercise(pipeline):
    metrics = {"some_status": "BAD"}
    assert pipeline._find_form_issue("Unknown Exercise", metrics) is None
