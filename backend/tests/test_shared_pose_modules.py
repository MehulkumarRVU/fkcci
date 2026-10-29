import sys
import os

# Ensure `backend` is on sys.path so `app.*` imports resolve during pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.pose_engine.shared.confidence import ConfidenceGate
from app.pose_engine.shared.mirroring import get_dominant_and_off_side, boxing_stance_sides
from app.pose_engine.shared.skill_profiles import widen_range, scale_penalty
from app.pose_engine.shared.reaction import measure_state_transition_reaction
from app.pose_engine.shared.normalization import normalize_landmarks
from app.pose_engine.shared.smoothing import smooth_landmarks
from app.pose_engine.analyzer_factory import AnalyzerFactory, NOT_YET_IMPLEMENTED, NOT_POSE_COACHABLE
from app.sports_registry import get_supported_sport_types


def make_landmarks(visibility=1.0):
    lm = []
    for i in range(33):
        lm.append({"x": float(i) * 0.01, "y": float(i) * 0.01, "z": 0.0, "visibility": visibility})
    return lm


# ---- ConfidenceGate ----

def test_confidence_gate_coverage_full_visibility():
    gate = ConfidenceGate()
    landmarks = make_landmarks(visibility=1.0)
    assert gate.coverage(landmarks) == 1.0


def test_confidence_gate_coverage_zero_visibility():
    gate = ConfidenceGate()
    landmarks = make_landmarks(visibility=0.0)
    assert gate.coverage(landmarks) == 0.0
    assert gate.is_confident(landmarks[0]) is False


def test_confidence_gate_partial_coverage():
    gate = ConfidenceGate()
    landmarks = make_landmarks(visibility=1.0)
    for i in range(0, 33, 2):
        landmarks[i]["visibility"] = 0.0
    coverage = gate.coverage(landmarks)
    assert 0.0 < coverage < 1.0


def test_confidence_gate_rejects_invalid_coordinates_and_missing_torso():
    gate = ConfidenceGate()
    landmarks = make_landmarks()
    landmarks[11]["x"] = float("nan")
    landmarks[23]["visibility"] = 0.0
    quality = gate.frame_quality(landmarks)
    assert quality["is_reliable"] is False
    assert "invalid_landmark_coordinates" in quality["reasons"]
    assert "torso_not_reliably_visible" in quality["reasons"]


def test_normalization_is_body_relative_and_preserves_visibility():
    landmarks = make_landmarks()
    normalized = normalize_landmarks(landmarks)
    assert abs((normalized[23]["x"] + normalized[24]["x"]) / 2) < 1e-9
    assert abs((normalized[23]["y"] + normalized[24]["y"]) / 2) < 1e-9
    assert normalized[0]["visibility"] == landmarks[0]["visibility"]


def test_smoothing_does_not_replace_occluded_landmark_with_previous_position():
    first = make_landmarks()
    second = make_landmarks()
    second[15]["visibility"] = 0.0
    second[15]["x"] = 0.0
    smoothed = smooth_landmarks([first, second])
    assert smoothed[1][15]["visibility"] == 0.0
    assert smoothed[1][15]["x"] == 0.0


# ---- Mirroring ----

def test_get_dominant_and_off_side_right():
    landmarks = make_landmarks()
    dom, off, side = get_dominant_and_off_side(landmarks, "right")
    assert side == "right"
    from app.pose_engine.shared.utils import PoseUtils
    assert dom.shoulder == landmarks[PoseUtils.LANDMARKS["RIGHT_SHOULDER"]]
    assert off.shoulder == landmarks[PoseUtils.LANDMARKS["LEFT_SHOULDER"]]


def test_get_dominant_and_off_side_left():
    landmarks = make_landmarks()
    dom, off, side = get_dominant_and_off_side(landmarks, "left")
    assert side == "left"
    from app.pose_engine.shared.utils import PoseUtils
    assert dom.shoulder == landmarks[PoseUtils.LANDMARKS["LEFT_SHOULDER"]]
    assert off.shoulder == landmarks[PoseUtils.LANDMARKS["RIGHT_SHOULDER"]]


def test_get_dominant_and_off_side_defaults_unknown_to_right():
    landmarks = make_landmarks()
    _dom, _off, side = get_dominant_and_off_side(landmarks, None)
    assert side == "right"


def test_boxing_stance_sides_orthodox_vs_southpaw():
    lead, power = boxing_stance_sides("right")
    assert (lead, power) == ("left", "right")  # orthodox: lead left, power right

    lead, power = boxing_stance_sides("left")
    assert (lead, power) == ("right", "left")  # southpaw: lead right, power left


# ---- Skill-level tolerance ----

def test_widen_range_beginner_wider_than_advanced():
    beg_low, beg_high = widen_range(140, 160, "beginner")
    adv_low, adv_high = widen_range(140, 160, "advanced")
    assert (beg_high - beg_low) > (adv_high - adv_low)


def test_scale_penalty_beginner_softer_than_advanced():
    assert scale_penalty(10.0, "beginner") < scale_penalty(10.0, "advanced")


# ---- Reaction score ----

def test_reaction_insufficient_data_for_short_sequence():
    score, status = measure_state_transition_reaction([90.0, 92.0])
    assert score is None
    assert status == "insufficient_data"


def test_reaction_not_measured_when_no_faults():
    score, status = measure_state_transition_reaction([95.0, 96.0, 94.0, 97.0])
    assert score is None
    assert status == "not_measured"


def test_reaction_measured_on_fault_then_recovery():
    # ready -> fault (drops below 70) -> recovers (back above 85)
    scores = [90.0, 90.0, 50.0, 50.0, 92.0, 92.0]
    score, status = measure_state_transition_reaction(scores)
    assert status == "measured"
    assert score is not None
    assert 0.0 <= score <= 100.0


# ---- AnalyzerFactory coverage across the full sports_registry ----

def test_every_registered_sport_resolves_without_crashing():
    landmarks = make_landmarks()
    for sport in get_supported_sport_types():
        analyzer = AnalyzerFactory.get_analyzer(sport)
        assert analyzer is not None
        result = analyzer.analyze_frame(landmarks, "Test Skill")
        assert isinstance(result, dict)

        if sport in NOT_YET_IMPLEMENTED or sport in NOT_POSE_COACHABLE:
            assert result.get("supported") is False
            assert result.get("score") is None
        else:
            assert result.get("score") is not None


def test_not_pose_coachable_sports_never_fake_a_score():
    landmarks = make_landmarks()
    for sport in NOT_POSE_COACHABLE:
        analyzer = AnalyzerFactory.get_analyzer(sport)
        result = analyzer.analyze_frame(landmarks, "Test Skill")
        assert result["supported"] is False
        assert result["reason"] == "not_pose_coachable"
        assert result["score"] is None
