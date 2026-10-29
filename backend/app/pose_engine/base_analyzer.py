from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from .shared.confidence import DEFAULT_GATE
from .shared.reaction import measure_state_transition_reaction
from .shared.scoring import CALIBRATION_STATUS
from .shared.skill_profiles import effective_max, effective_min, scale_penalty, widen_range
from .shared.smoothing import reject_low_confidence_frames, smooth_landmarks, smooth_series


class BaseAnalyzer(ABC):
    """Base class for all pose analyzers.

    Provides shared, skill-level-aware scoring primitives (`check_range`,
    `check_min`, `check_max`, `blend_scores`), a `analyze_frame_full` wrapper
    that attaches pose_confidence/calibration_status to any subclass's result
    without each subclass having to compute them, and a shared
    session-aggregation implementation (landmark smoothing, low-confidence
    frame rejection, outlier-rejecting score smoothing, and a real
    event-based reaction_score) - so per-sport analyzers stop each
    reimplementing the same threshold-check shape and flat-average
    aggregation independently.
    """

    def __init__(self, sport_type: str):
        self.sport_type = sport_type

    @abstractmethod
    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str,
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        """Analyze a single frame of pose landmarks."""
        raise NotImplementedError

    @abstractmethod
    def get_supported_skills(self) -> List[str]:
        """Return supported skill names for this analyzer."""
        raise NotImplementedError

    # ---- Shared, skill-level-aware scoring helpers ----

    def check_range(self, value: Optional[float], low: float, high: float, skill_level: str,
                     penalty: float, pass_msg: str, low_msg: Optional[str] = None,
                     high_msg: Optional[str] = None, low_penalty: Optional[float] = None,
                     high_penalty: Optional[float] = None) -> Tuple[float, Optional[str]]:
        """Score a value expected to fall within [low, high]. The range widens
        for beginners and narrows for advanced athletes. `value` of None
        (landmark not confidently visible) is skipped rather than scored
        against garbage input - returns (0.0, None). `low_penalty`/`high_penalty`
        allow an asymmetric penalty depending on which side fails (falls back
        to `penalty` when not given)."""
        if value is None:
            return 0.0, None
        adj_low, adj_high = widen_range(low, high, skill_level)
        if adj_low <= value <= adj_high:
            return 0.0, pass_msg
        if value < adj_low:
            p = low_penalty if low_penalty is not None else penalty
            return -scale_penalty(p, skill_level), (low_msg or high_msg)
        p = high_penalty if high_penalty is not None else penalty
        return -scale_penalty(p, skill_level), (high_msg or low_msg)

    def check_min(self, value: Optional[float], minimum: float, skill_level: str,
                   penalty: float, pass_msg: str, fail_msg: str) -> Tuple[float, Optional[str]]:
        """Score a value expected to be >= minimum (e.g. extension angle)."""
        if value is None:
            return 0.0, None
        threshold = effective_min(minimum, skill_level)
        if value >= threshold:
            return 0.0, pass_msg
        return -scale_penalty(penalty, skill_level), fail_msg

    def check_max(self, value: Optional[float], maximum: float, skill_level: str,
                   penalty: float, pass_msg: str, fail_msg: str) -> Tuple[float, Optional[str]]:
        """Score a value expected to be <= maximum."""
        if value is None:
            return 0.0, None
        threshold = effective_max(maximum, skill_level)
        if value <= threshold:
            return 0.0, pass_msg
        return -scale_penalty(penalty, skill_level), fail_msg

    @staticmethod
    def blend_scores(technique_score: float, balance_score: float, technique_weight: float) -> float:
        return max(0.0, technique_score * technique_weight + balance_score * (1 - technique_weight))

    # ---- Confidence / calibration wrapper ----

    def analyze_frame_full(self, landmarks: List[Dict[str, float]], skill_name: str,
                            skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        """Runs analyze_frame and attaches pose_confidence and
        calibration_status as distinct fields, without requiring every
        subclass to compute them itself. This is what routes/services should
        call for API responses; analyze_frame stays the simpler internal
        per-frame primitive used inside analyze_session."""
        result = dict(self.analyze_frame(landmarks, skill_name, skill_level, dominant_hand))
        quality = DEFAULT_GATE.frame_quality(landmarks)
        result["pose_confidence"] = round(float(quality["coverage"]), 2)
        result["evaluation_status"] = "reliable" if quality["is_reliable"] else "insufficient_evidence"
        result["reliability_reasons"] = list(quality["reasons"])
        if not quality["is_reliable"]:
            result["score"] = None
            result["technique_accuracy"] = None
            result["balance_score"] = None
            result["feedback"] = [
                "⚠️ Unable to evaluate reliably - move fully into frame and repeat the movement."
            ]
        result.setdefault("calibration_status", CALIBRATION_STATUS)
        return result

    # ---- Shared session aggregation ----

    def analyze_session(self, pose_sequence: List[List[Dict[str, float]]], skill_name: str,
                         skill_level: str = "beginner", dominant_hand: str = "right",
                         timestamps: Optional[List[float]] = None) -> Dict[str, Any]:
        """Default session analysis shared by every analyzer: reject frames
        with too little visible landmark coverage to trust, EMA-smooth the
        remaining landmarks to reduce jitter, score each frame, then apply
        outlier-rejecting/smoothed aggregation (not a naive flat average)
        plus a real event-based reaction_score derived from fault-recovery
        timing (or an honest null when there isn't enough signal to measure).

        Subclasses that need sport-specific counters (reps/combos/jumps)
        should call `super().analyze_session(...)` and merge extra `detailed`
        keys into the result rather than reimplementing aggregation.
        """
        frame_qualities = [DEFAULT_GATE.frame_quality(frame) for frame in pose_sequence]
        overall_coverage = (
            sum(float(q["coverage"]) for q in frame_qualities) / len(frame_qualities)
            if frame_qualities else 0.0
        )

        kept_frames, kept_timestamps = reject_low_confidence_frames(pose_sequence, timestamps)
        if not kept_frames:
            return {
                "overall_score": None,
                "technique_accuracy": None,
                "balance_score": None,
                "reaction_score": None,
                "reaction_status": "insufficient_data",
                "pose_confidence": round(overall_coverage, 2),
                "calibration_status": CALIBRATION_STATUS,
                "frame_count": 0,
                "evaluation_status": "insufficient_evidence",
                "reliability_reasons": ["no_reliably_visible_frames"],
            }

        smoothed_frames = smooth_landmarks(kept_frames)
        frame_results = [
            self.analyze_frame_full(frame, skill_name, skill_level, dominant_hand)
            for frame in smoothed_frames
        ]

        reliable_results = [r for r in frame_results if r.get("score") is not None]
        if not reliable_results:
            return {
                "overall_score": None,
                "technique_accuracy": None,
                "balance_score": None,
                "reaction_score": None,
                "reaction_status": "insufficient_data",
                "pose_confidence": round(overall_coverage, 2),
                "calibration_status": CALIBRATION_STATUS,
                "frame_count": 0,
                "evaluation_status": "insufficient_evidence",
                "reliability_reasons": ["no_reliably_scored_frames"],
            }

        scores = [r["score"] for r in reliable_results]
        tech = [r["technique_accuracy"] for r in reliable_results]
        bal = [r["balance_score"] for r in reliable_results]

        smoothed_scores = smooth_series(scores)
        smoothed_tech = smooth_series(tech)
        smoothed_bal = smooth_series(bal)

        avg_score = sum(smoothed_scores) / len(smoothed_scores)
        avg_tech = sum(smoothed_tech) / len(smoothed_tech)
        avg_balance = sum(smoothed_bal) / len(smoothed_bal)
        reaction_score, reaction_status = measure_state_transition_reaction(smoothed_tech, kept_timestamps)

        return {
            "overall_score": round(avg_score, 2),
            "technique_accuracy": round(avg_tech, 2),
            "balance_score": round(avg_balance, 2),
            "reaction_score": None if reaction_score is None else round(reaction_score, 2),
            "reaction_status": reaction_status,
            "pose_confidence": round(overall_coverage, 2),
            "calibration_status": CALIBRATION_STATUS,
            "frame_count": len(frame_results),
            "evaluation_status": "reliable",
            "reliability_reasons": [],
        }
