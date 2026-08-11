from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.athlete import Athlete
from ..models.coach_note import CoachNote
from .auth import get_current_athlete

router = APIRouter(prefix="/api/notes", tags=["Notes"])


class NoteCreate(BaseModel):
    message: str
    session_id: Optional[int] = None


class NoteOut(BaseModel):
    id: int
    athlete_id: int
    author_id: int
    author_username: str
    is_coach: bool
    session_id: Optional[int]
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


def _check_thread_access(athlete_id: int, current_athlete: Athlete, db: Session) -> Athlete:
    """A thread is scoped to one athlete; only that athlete or their
    assigned coach may read/write it - same relationship-check pattern
    already used in analytics.py (athlete.coach_id == current_athlete.id)."""
    athlete = db.query(Athlete).filter(Athlete.id == athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")

    is_self = current_athlete.id == athlete_id
    is_their_coach = athlete.coach_id == current_athlete.id
    if not (is_self or is_their_coach):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this thread")

    return athlete


@router.get("/athlete/{athlete_id}", response_model=List[NoteOut])
async def get_notes(
    athlete_id: int,
    session_id: Optional[int] = None,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    _check_thread_access(athlete_id, current_athlete, db)

    query = db.query(CoachNote).filter(CoachNote.athlete_id == athlete_id)
    if session_id is not None:
        query = query.filter(CoachNote.session_id == session_id)
    notes = query.order_by(CoachNote.created_at.asc()).all()

    author_ids = {n.author_id for n in notes}
    authors = {a.id: a for a in db.query(Athlete).filter(Athlete.id.in_(author_ids)).all()} if author_ids else {}

    return [
        NoteOut(
            id=n.id,
            athlete_id=n.athlete_id,
            author_id=n.author_id,
            author_username=authors[n.author_id].username if n.author_id in authors else "Unknown",
            is_coach=authors[n.author_id].role == "coach" if n.author_id in authors else False,
            session_id=n.session_id,
            message=n.message,
            created_at=n.created_at,
        )
        for n in notes
    ]


@router.post("/athlete/{athlete_id}", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def post_note(
    athlete_id: int,
    note: NoteCreate,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    _check_thread_access(athlete_id, current_athlete, db)

    if not note.message or not note.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    new_note = CoachNote(
        athlete_id=athlete_id,
        author_id=current_athlete.id,
        session_id=note.session_id,
        message=note.message.strip(),
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return NoteOut(
        id=new_note.id,
        athlete_id=new_note.athlete_id,
        author_id=new_note.author_id,
        author_username=current_athlete.username,
        is_coach=current_athlete.role == "coach",
        session_id=new_note.session_id,
        message=new_note.message,
        created_at=new_note.created_at,
    )
