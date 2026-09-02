from sqlalchemy.orm import Session
from ..models.skill import Skill


class SkillRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_active(self, sport_type: str | None = None, difficulty_level: str | None = None):
        query = self.db.query(Skill).filter(Skill.is_active == True)
        if sport_type:
            query = query.filter(Skill.sport_type == sport_type)
        if difficulty_level:
            query = query.filter(Skill.difficulty_level == difficulty_level)
        return query.all()

    def get_by_id(self, skill_id: int) -> Skill | None:
        return self.db.query(Skill).filter(Skill.id == skill_id, Skill.is_active == True).first()

    def create(self, skill: Skill) -> Skill:
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return skill
