from sqlalchemy.orm import Session
from ..models.athlete import Athlete


class AthleteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Athlete | None:
        return self.db.query(Athlete).filter(Athlete.email == email).first()

    def get_by_username(self, username: str) -> Athlete | None:
        return self.db.query(Athlete).filter(Athlete.username == username).first()

    def get_by_id(self, athlete_id: int) -> Athlete | None:
        return self.db.query(Athlete).filter(Athlete.id == athlete_id).first()

    def create(self, athlete: Athlete) -> Athlete:
        self.db.add(athlete)
        self.db.commit()
        self.db.refresh(athlete)
        return athlete

    def save(self, athlete: Athlete) -> Athlete:
        self.db.commit()
        self.db.refresh(athlete)
        return athlete
