from app.adaptive_training import (
    AdaptiveAnalysisConfig,
    AdaptiveProfileInput,
    evaluate_adaptive_frame,
    exercise_catalog,
    is_exercise_supported,
)


def _upper_body_frame():
    frame = [{"x": 0.0, "y": 0.0, "z": 0.0, "visibility": 0.0} for _ in range(33)]
    # Shoulder -> elbow -> wrist form a measurable straight arm.
    for index, x, y in ((11, 0.2, 0.4), (13, 0.2, 0.6), (15, 0.2, 0.8),
                        (12, 0.8, 0.4), (14, 0.8, 0.6), (16, 0.8, 0.8)):
        frame[index] = {"x": x, "y": y, "z": 0.0, "visibility": 0.95}
    return frame


def test_adaptive_catalog_exposes_supported_setups_without_new_category():
    exercise = exercise_catalog("table_tennis")["adaptive_racket_arm"]
    assert exercise["setups"] == ["standing", "seated", "wheelchair"]
    assert "required_landmarks" in exercise


def test_adaptive_exercise_support_is_category_specific():
    assert is_exercise_supported("boxing", "adaptive_punch")
    assert not is_exercise_supported("calisthenics", "adaptive_punch")
    assert not exercise_catalog("calisthenics")


def test_seated_adaptive_analysis_uses_partial_upper_body_requirements():
    config = AdaptiveAnalysisConfig(
        setup="seated",
        exercise="adaptive_racket_arm",
        camera_view="front",
    )
    result = evaluate_adaptive_frame(_upper_body_frame(), config)
    assert result["evaluation_status"] == "reliable"
    assert result["score"] is not None


def test_adaptive_analysis_rejects_missing_required_landmarks_without_score():
    config = AdaptiveAnalysisConfig(
        setup="wheelchair",
        exercise="adaptive_racket_arm",
        camera_view="front",
    )
    frame = _upper_body_frame()
    frame[15]["visibility"] = 0.0
    result = evaluate_adaptive_frame(frame, config)
    assert result["score"] is None
    assert result["evaluation_status"] == "insufficient_evidence"


def test_adaptive_profile_does_not_require_medical_information():
    profile = AdaptiveProfileInput(enabled=True, preferred_setup="seated")
    assert profile.enabled is True
    assert profile.model_dump()["approved_reference"] is None
