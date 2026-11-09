from datetime import datetime
from typing import List, Optional
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.athlete import Athlete
from ..models.coach_connection_request import CoachConnectionRequest
from ..models.coach_invite import CoachInvite
from .auth import get_current_athlete
from ..time_utils import utc_now

router = APIRouter(prefix="/api/coaches", tags=["Coaches"])


def _require_role(athlete: Athlete, role: str) -> None:
    if athlete.role != role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Only {role}s can perform this action")


class CoachSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str

class AthleteSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    sport_type: str

class ConnectionRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    athlete_id: int
    coach_id: int
    status: str
    created_at: datetime
    responded_at: Optional[datetime] = None
    athlete: Optional[AthleteSummary] = None
    coach: Optional[CoachSummary] = None

class ConnectionStatusOut(BaseModel):
    connected_coach: Optional[CoachSummary] = None
    pending_request: Optional[ConnectionRequestOut] = None


class InviteCodeOut(BaseModel):
    code: str
    created_at: datetime


@router.get("/search", response_model=List[CoachSummary])
def search_coaches(
    q: str = "",
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    _require_role(current_athlete, "athlete")

    query = db.query(Athlete).filter(Athlete.role == "coach")
    if q.strip():
        query = query.filter(Athlete.username.ilike(f"%{q.strip()}%"))
    coaches = query.order_by(Athlete.username.asc()).limit(20).all()
    return coaches


@router.post("/{coach_id}/request", response_model=ConnectionRequestOut, status_code=status.HTTP_201_CREATED)
def request_coach(
    coach_id: int,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    _require_role(current_athlete, "athlete")

    if current_athlete.coach_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already have a coach")

    existing_pending = db.query(CoachConnectionRequest).filter(
        CoachConnectionRequest.athlete_id == current_athlete.id,
        CoachConnectionRequest.status == "pending",
    ).first()
    if existing_pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already have a pending request")

    coach = db.query(Athlete).filter(Athlete.id == coach_id, Athlete.role == "coach").first()
    if not coach:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coach not found")

    new_request = CoachConnectionRequest(athlete_id=current_athlete.id, coach_id=coach_id, status="pending")
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request


@router.get("/me/requests", response_model=List[ConnectionRequestOut])
def list_pending_requests(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    _require_role(current_athlete, "coach")

    requests = db.query(CoachConnectionRequest).filter(
        CoachConnectionRequest.coach_id == current_athlete.id,
        CoachConnectionRequest.status == "pending",
    ).order_by(CoachConnectionRequest.created_at.asc()).all()

    athlete_ids = {r.athlete_id for r in requests}
    athletes = {a.id: a for a in db.query(Athlete).filter(Athlete.id.in_(athlete_ids)).all()} if athlete_ids else {}

    result = []
    for r in requests:
        out = ConnectionRequestOut.model_validate(r)
        if r.athlete_id in athletes:
            out.athlete = AthleteSummary.model_validate(athletes[r.athlete_id])
        result.append(out)
    return result


def _get_own_request_as_coach(request_id: int, current_athlete: Athlete, db: Session) -> CoachConnectionRequest:
    req = db.query(CoachConnectionRequest).filter(
        CoachConnectionRequest.id == request_id, CoachConnectionRequest.coach_id == current_athlete.id
    ).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if req.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request already resolved")
    return req


@router.post("/requests/{request_id}/accept", response_model=ConnectionRequestOut)
def accept_request(
    request_id: int,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    _require_role(current_athlete, "coach")
    req = _get_own_request_as_coach(request_id, current_athlete, db)

    athlete = db.query(Athlete).filter(Athlete.id == req.athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    if athlete.coach_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Athlete already has a coach")

    req.status = "accepted"
    req.responded_at = utc_now()
    athlete.coach_id = current_athlete.id
    db.commit()
    db.refresh(req)
    return req


@router.post("/requests/{request_id}/reject", response_model=ConnectionRequestOut)
def reject_request(
    request_id: int,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    _require_role(current_athlete, "coach")
    req = _get_own_request_as_coach(request_id, current_athlete, db)

    req.status = "rejected"
    req.responded_at = utc_now()
    db.commit()
    db.refresh(req)
    return req


@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_request(
    request_id: int,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    req = db.query(CoachConnectionRequest).filter(
        CoachConnectionRequest.id == request_id, CoachConnectionRequest.athlete_id == current_athlete.id
    ).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if req.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request already resolved")

    db.delete(req)
    db.commit()


@router.post("/me/invite-code", response_model=InviteCodeOut)
def generate_invite_code(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    _require_role(current_athlete, "coach")

    db.query(CoachInvite).filter(
        CoachInvite.coach_id == current_athlete.id, CoachInvite.revoked == False
    ).update({"revoked": True})

    code = secrets.token_urlsafe(6)
    invite = CoachInvite(coach_id=current_athlete.id, code=code, revoked=False)
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return InviteCodeOut(code=invite.code, created_at=invite.created_at)


@router.get("/me/invite-code", response_model=Optional[InviteCodeOut])
def get_invite_code(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    _require_role(current_athlete, "coach")

    invite = db.query(CoachInvite).filter(
        CoachInvite.coach_id == current_athlete.id, CoachInvite.revoked == False
    ).order_by(CoachInvite.created_at.desc()).first()
    if not invite:
        return None
    return InviteCodeOut(code=invite.code, created_at=invite.created_at)


@router.post("/join/{code}", response_model=CoachSummary)
def join_with_code(
    code: str,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    _require_role(current_athlete, "athlete")

    if current_athlete.coach_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already have a coach")

    invite = db.query(CoachInvite).filter(CoachInvite.code == code, CoachInvite.revoked == False).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired invite code")

    coach = db.query(Athlete).filter(Athlete.id == invite.coach_id, Athlete.role == "coach").first()
    if not coach:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coach not found")

    current_athlete.coach_id = coach.id
    db.commit()
    return coach


@router.delete("/me/athletes/{athlete_id}", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_athlete(
    athlete_id: int,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    _require_role(current_athlete, "coach")

    athlete = db.query(Athlete).filter(Athlete.id == athlete_id, Athlete.coach_id == current_athlete.id).first()
    if not athlete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")

    athlete.coach_id = None
    db.commit()


@router.post("/me/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_coach(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    _require_role(current_athlete, "athlete")

    if current_athlete.coach_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You don't have a coach")

    current_athlete.coach_id = None
    db.commit()


@router.get("/me/connection-status", response_model=ConnectionStatusOut)
def connection_status(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    _require_role(current_athlete, "athlete")

    if current_athlete.coach_id is not None:
        coach = db.query(Athlete).filter(Athlete.id == current_athlete.coach_id).first()
        return ConnectionStatusOut(connected_coach=coach)

    pending = db.query(CoachConnectionRequest).filter(
        CoachConnectionRequest.athlete_id == current_athlete.id,
        CoachConnectionRequest.status == "pending",
    ).first()
    if pending:
        out = ConnectionRequestOut.model_validate(pending)
        coach = db.query(Athlete).filter(Athlete.id == pending.coach_id).first()
        if coach:
            out.coach = CoachSummary.model_validate(coach)
        return ConnectionStatusOut(pending_request=out)

    return ConnectionStatusOut()
