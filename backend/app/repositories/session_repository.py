from sqlalchemy.orm import Session
from ..models.session import Session as SessionModel


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, session: SessionModel) -> SessionModel:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_by_id(self, session_id: int) -> SessionModel | None:
        return self.db.query(SessionModel).filter(SessionModel.id == session_id).first()

    def list_for_athlete(self, athlete_id: int, skip: int = 0, limit: int = 50):
        return (
            self.db.query(SessionModel)
            .filter(SessionModel.athlete_id == athlete_id)
            .order_by(SessionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def delete(self, session: SessionModel):
        self.db.delete(session)
        self.db.commit()

    def save(self, session: SessionModel):
        self.db.commit()
        self.db.refresh(session)
        return session
