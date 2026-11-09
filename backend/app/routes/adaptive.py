from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..adaptive_training import (
    ACTIVE_ADAPTIVE_CATEGORIES,
    AdaptiveProfileInput,
    exercise_catalog,
)
from ..database import get_db
from ..models.athlete import Athlete
from .auth import get_current_athlete

router = APIRouter(prefix="/api/adaptive", tags=["Adaptive Training"])


@router.get("/catalog")
def get_adaptive_catalog(category: Optional[str] = None) -> Dict[str, Any]:
    if category and category not in ACTIVE_ADAPTIVE_CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid training category")
    return {
        "categories": sorted(ACTIVE_ADAPTIVE_CATEGORIES),
        "exercises": exercise_catalog(category),
        "status": "implemented_foundation",
        "limitations": [
            "No disability, diagnosis, or Paralympic eligibility is inferred from video.",
            "Racket contact and sport-specific stroke recognition are not validated.",
        ],
    }


@router.get("/profile")
def get_adaptive_profile(
    current_athlete: Athlete = Depends(get_current_athlete),
) -> Dict[str, Any]:
    return {
        "enabled": bool(current_athlete.adaptive_mode_enabled),
        "profile": current_athlete.adaptive_profile,
    }


@router.put("/profile")
def update_adaptive_profile(
    profile: AdaptiveProfileInput,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    current_athlete.adaptive_mode_enabled = profile.enabled
    current_athlete.adaptive_profile = profile.model_dump(exclude={"enabled"})
    db.commit()
    db.refresh(current_athlete)
    return {
        "enabled": current_athlete.adaptive_mode_enabled,
        "profile": current_athlete.adaptive_profile,
    }


@router.delete("/profile", status_code=204)
def delete_adaptive_profile(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    current_athlete.adaptive_mode_enabled = False
    current_athlete.adaptive_profile = None
    db.commit()


class AdaptiveCapabilityResponse(BaseModel):
    category: str
    adaptive_supported: bool
    note: str


@router.get("/capabilities", response_model=list[AdaptiveCapabilityResponse])
def adaptive_capabilities():
    capabilities = []
    for category in sorted(ACTIVE_ADAPTIVE_CATEGORIES):
        supported = bool(exercise_catalog(category))
        capabilities.append(AdaptiveCapabilityResponse(
            category=category,
            adaptive_supported=supported,
            note=(
                "Configurable references with required-landmark gating; validate with coaches and athletes before sport-specific claims."
                if supported else "No adaptive exercise is currently available for this category."
            ),
        ))
    return capabilities
