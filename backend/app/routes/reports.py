from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.session import Session as SessionModel
from ..models.athlete import Athlete
from ..services.pdf_service import build_session_report, build_progress_report, build_coach_athlete_report
from ..services.profile_twin_service import get_athlete_twin
from .auth import get_current_athlete
from .sessions import get_session_stats
from .analytics import build_athlete_monthly_report

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def _pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/session/{session_id}/pdf")
async def download_session_report(
    session_id: int,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    """PDF report for one of the current athlete's own sessions."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.athlete_id != current_athlete.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    pdf_bytes = build_session_report(session, current_athlete)
    return _pdf_response(pdf_bytes, f"session_{session_id}_report.pdf")


@router.get("/progress/pdf")
async def download_progress_report(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    """PDF progress report for the current athlete, reusing the same
    profile-twin aggregation and session-stats summary already used
    elsewhere - no new aggregation logic."""
    twin_data = get_athlete_twin(current_athlete.id, db)
    stats = await get_session_stats(current_athlete=current_athlete, db=db)

    pdf_bytes = build_progress_report(current_athlete, twin_data, stats)
    return _pdf_response(pdf_bytes, f"{current_athlete.username}_progress_report.pdf")


@router.get("/coach/athlete/{athlete_id}/pdf")
async def download_coach_athlete_report(
    athlete_id: int,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    """Coach-only PDF report for one of their athletes, reusing the exact
    same 30-day aggregation as the JSON monthly-report endpoint."""
    report = build_athlete_monthly_report(athlete_id, current_athlete, db)
    pdf_bytes = build_coach_athlete_report(report)
    return _pdf_response(pdf_bytes, f"{report.athlete_username}_coach_report.pdf")
