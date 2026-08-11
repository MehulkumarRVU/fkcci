"""Single reusable scoring formula shared by every analyzer, replacing the
previously duplicated `technique_score * W + balance_score * (1 - W)`
pattern copy-pasted into all 12 sport analyzers.

Keeps pose_confidence, technique_score, balance_score, performance_score,
reaction_score (nullable), and calibration_status as distinct, separately
labeled fields instead of blending everything into one opaque number - so a
low score can always be traced back to "couldn't see you" vs "bad technique"
vs "bad balance" vs a real reaction-time signal.
"""
from dataclasses import dataclass, field
from typing import List, Optional

# Tags which scoring engine generation produced a result. "heuristic_v2_biomechanics"
# is this rule-based, skill-level-aware engine; "ml_v1" is reserved for a future
# data-calibrated/ML-trained scorer so historical results stay distinguishable
# once one exists.
CALIBRATION_STATUS = "heuristic_v2_biomechanics"


@dataclass
class CheckResult:
    passed: bool
    delta: float
    message: Optional[str] = None


@dataclass
class ScoreBreakdown:
    pose_confidence: float
    technique_score: float
    balance_score: float
    performance_score: float
    reaction_score: Optional[float]
    reaction_status: str  # "measured" | "not_measured" | "insufficient_data"
    calibration_status: str = CALIBRATION_STATUS
    feedback: List[str] = field(default_factory=list)
    joint_angles: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "score": round(self.performance_score, 2),
            "technique_accuracy": round(self.technique_score, 2),
            "balance_score": round(self.balance_score, 2),
            "pose_confidence": round(self.pose_confidence, 2),
            "reaction_score": None if self.reaction_score is None else round(self.reaction_score, 2),
            "reaction_status": self.reaction_status,
            "calibration_status": self.calibration_status,
            "feedback": self.feedback,
            "joint_angles": self.joint_angles,
        }


def combine_scores(technique_score: float, balance_score: float, technique_weight: float,
                    pose_confidence: float = 1.0, reaction_score: Optional[float] = None,
                    reaction_status: str = "not_measured", feedback: Optional[List[str]] = None,
                    joint_angles: Optional[dict] = None) -> ScoreBreakdown:
    technique_score = max(0.0, technique_score)
    performance = max(0.0, technique_score * technique_weight + balance_score * (1 - technique_weight))
    return ScoreBreakdown(
        pose_confidence=pose_confidence,
        technique_score=technique_score,
        balance_score=balance_score,
        performance_score=performance,
        reaction_score=reaction_score,
        reaction_status=reaction_status,
        feedback=feedback or [],
        joint_angles=joint_angles or {},
    )
