from sqlalchemy import Column, Integer, String, JSON, Text, DateTime, ForeignKey
from datetime import datetime
from ..database import Base


class SkillReferencePose(Base):
    """Structured "ideal form" reference for a skill: target joint-angle
    ranges per skill_level. Documents the same ranges the analyzer checks
    against (see pose_engine/sports/*.py), so a coach-facing UI can show
    "what good form looks like" without re-deriving it. Live per-frame
    deviation classification (shared/reference_compare.py) uses the
    analyzer's own thresholds directly rather than reading this table on
    every frame - this is the authored/documented record, not a runtime
    config store.
    """
    __tablename__ = "skill_reference_poses"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    skill_level = Column(String, nullable=False, default="beginner")
    checkpoint_name = Column(String, nullable=False, default="default")
    joint_angle_ranges = Column(JSON, nullable=False)  # e.g. {"arm_extension": [130, 170]}
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
