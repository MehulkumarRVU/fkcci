"""Validated, non-diagnostic adaptive training configuration and evaluation."""
import math
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, model_validator

from .pose_engine.shared.confidence import DEFAULT_GATE


ACTIVE_ADAPTIVE_CATEGORIES = {
    "boxing",
    "table_tennis",
    "gym",
    "badminton",
    "stretching",
    "mobility_training",
    "rehabilitation",
    "home_workouts",
    "calisthenics",
}

SETUPS = {"standing", "seated", "wheelchair"}

EXERCISES: Dict[str, Dict[str, Any]] = {
    "seated_upper_body_reach": {
        "categories": ["gym", "home_workouts", "rehabilitation", "mobility_training"],
        "setups": ["seated", "wheelchair"],
        "required_landmarks": [11, 12, 13, 14, 15, 16],
        "camera_views": ["front", "side"],
        "feature": "left_elbow_angle",
        "default_target": {"min": 120.0, "max": 180.0},
    },
    "standing_upper_body_reach": {
        "categories": ["gym", "home_workouts", "stretching", "mobility_training", "rehabilitation"],
        "setups": ["standing"],
        "required_landmarks": [11, 12, 13, 14, 15, 16],
        "camera_views": ["front", "side"],
        "feature": "left_elbow_angle",
        "default_target": {"min": 120.0, "max": 180.0},
    },
    "adaptive_punch": {
        "categories": ["boxing"],
        "setups": ["standing", "seated", "wheelchair"],
        "required_landmarks": [11, 13, 15],
        "camera_views": ["front", "side"],
        "feature": "left_elbow_angle",
        "default_target": {"min": 100.0, "max": 180.0},
    },
    "adaptive_racket_arm": {
        "categories": ["table_tennis", "badminton"],
        "setups": ["standing", "seated", "wheelchair"],
        "required_landmarks": [11, 13, 15],
        "camera_views": ["front", "side"],
        "feature": "left_elbow_angle",
        "default_target": {"min": 90.0, "max": 180.0},
    },
}


class AdaptiveReference(BaseModel):
    min: float = Field(ge=0, le=180)
    max: float = Field(ge=0, le=180)
    approved_by: Optional[str] = Field(default=None, max_length=120)
    version: str = Field(default="adaptive_rules_v1", max_length=40)

    @model_validator(mode="after")
    def valid_range(self):
        if self.min > self.max:
            raise ValueError("reference min must not exceed max")
        return self


class AdaptiveProfileInput(BaseModel):
    enabled: bool = False
    preferred_setup: Optional[str] = None
    exercise_adaptations: List[str] = Field(default_factory=list, max_length=20)
    relevant_landmarks: List[int] = Field(default_factory=list, max_length=33)
    movement_targets: Dict[str, float] = Field(default_factory=dict)
    equipment: List[str] = Field(default_factory=list, max_length=20)
    camera_view: Optional[str] = None
    training_goals: List[str] = Field(default_factory=list, max_length=10)
    accessibility_preferences: List[str] = Field(default_factory=list, max_length=20)
    approved_reference: Optional[AdaptiveReference] = None

    @model_validator(mode="after")
    def validate_setup(self):
        if self.preferred_setup and self.preferred_setup not in SETUPS:
            raise ValueError(f"preferred_setup must be one of: {', '.join(sorted(SETUPS))}")
        return self


class AdaptiveAnalysisConfig(BaseModel):
    setup: str
    exercise: str
    camera_view: str
    reference: Optional[AdaptiveReference] = None

    @model_validator(mode="after")
    def validate_values(self):
        if self.setup not in SETUPS:
            raise ValueError(f"setup must be one of: {', '.join(sorted(SETUPS))}")
        if self.exercise not in EXERCISES:
            raise ValueError("unsupported adaptive exercise")
        if self.camera_view not in EXERCISES[self.exercise]["camera_views"]:
            raise ValueError("camera view is not validated for this exercise")
        if self.setup not in EXERCISES[self.exercise]["setups"]:
            raise ValueError("setup is not validated for this exercise")
        return self


def exercise_catalog(category: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    return {
        key: value for key, value in EXERCISES.items()
        if category is None or category in value["categories"]
    }


def required_landmarks(exercise: str) -> List[int]:
    return list(EXERCISES[exercise]["required_landmarks"])


def _angle(a: Dict[str, float], b: Dict[str, float], c: Dict[str, float]) -> Optional[float]:
    vectors = ((float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"])),
               (float(c["x"]) - float(b["x"]), float(c["y"]) - float(b["y"])))
    lengths = [math.hypot(*vector) for vector in vectors]
    if not all(length > 0 for length in lengths):
        return None
    cosine = sum(x * y for x, y in zip(vectors[0], vectors[1])) / (lengths[0] * lengths[1])
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def evaluate_adaptive_frame(
    landmarks: List[Dict[str, float]],
    config: AdaptiveAnalysisConfig,
) -> Dict[str, Any]:
    required = required_landmarks(config.exercise)
    quality = DEFAULT_GATE.frame_quality(landmarks, min_coverage=1.0, required_indices=required)
    if not quality["is_reliable"]:
        return {
            "score": None,
            "evaluation_status": "insufficient_evidence",
            "pose_confidence": round(float(quality["coverage"]), 2),
            "reliability_reasons": list(quality["reasons"]),
            "feedback": ["Unable to evaluate this adaptive movement; adjust the camera so the required upper-body landmarks are visible."],
        }

    angle = _angle(landmarks[11], landmarks[13], landmarks[15])
    reference = config.reference or AdaptiveReference(**EXERCISES[config.exercise]["default_target"])
    if angle is None:
        return {
            "score": None,
            "evaluation_status": "ambiguous_observation",
            "pose_confidence": 1.0,
            "reliability_reasons": ["ambiguous_joint_geometry"],
            "feedback": ["This movement angle could not be measured reliably from the selected camera view."],
        }
    distance = 0.0 if reference.min <= angle <= reference.max else min(
        abs(angle - reference.min), abs(angle - reference.max)
    )
    score = round(max(0.0, 100.0 - distance * 2.0), 2)
    return {
        "score": score,
        "evaluation_status": "reliable",
        "pose_confidence": 1.0,
        "reliability_reasons": [],
        "feedback": ["Movement is within the selected reference." if distance == 0 else
                     "Movement differs from the selected reference; compare against your approved target."],
        "observed_features": {"left_elbow_angle": round(angle, 2)},
        "reference": reference.model_dump(),
        "scoring_version": reference.version,
    }
