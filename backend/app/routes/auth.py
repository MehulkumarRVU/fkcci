from datetime import datetime, timedelta
import base64
import hashlib
import hmac
import logging
import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.athlete import Athlete
from ..config import settings
from ..sports_registry import is_valid_sport, VALID_SPORTS
from ..services.auth_service import AuthService
from ..services.email_service import send_password_reset_email

try:
    import bcrypt
except ImportError:
    bcrypt = None

# Security Configuration (loaded from environment via settings)
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_DAYS = settings.ACCESS_TOKEN_EXPIRE_DAYS
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# Pydantic Models
class AthleteCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    sport_type: str  # table_tennis, boxing, or badminton
    skill_level: Optional[str] = "beginner"
    dominant_hand: Optional[str] = "right"
    height: Optional[float] = None
    weight: Optional[float] = None


class CoachCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class CoachResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class AthleteResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    coach_id: Optional[int] = None
    sport_type: str
    linked_sports: List[str]
    skill_level: str
    dominant_hand: str
    height: Optional[float] = None
    weight: Optional[float] = None
    training_frequency_per_week: int = 0
    membership_tier: str
    total_sessions: int
    performance_rating: float
    created_at: datetime


class AthleteProfileUpdate(BaseModel):
    sport_type: Optional[str] = None
    linked_sports: Optional[List[str]] = None
    skill_level: Optional[str] = None
    dominant_hand: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    training_frequency_per_week: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None




def normalize_linked_sports(linked_sports: Optional[List[str]]) -> List[str]:
    if not linked_sports:
        return []

    normalized = []
    for sport in linked_sports:
        if sport in VALID_SPORTS and sport not in normalized:
            normalized.append(sport)
    return normalized


def athlete_to_response(athlete: Athlete) -> AthleteResponse:
    linked_sports = [sport for sport in (athlete.linked_sports or "").split(",") if sport]
    if athlete.sport_type and athlete.sport_type not in linked_sports:
        linked_sports.append(athlete.sport_type)

    return AthleteResponse(
        id=athlete.id,
        email=athlete.email,
        username=athlete.username,
        role=athlete.role,
        coach_id=athlete.coach_id,
        sport_type=athlete.sport_type,
        linked_sports=linked_sports,
        skill_level=athlete.skill_level,
        dominant_hand=athlete.dominant_hand,
        height=athlete.height,
        weight=athlete.weight,
        training_frequency_per_week=athlete.training_frequency_per_week,
        membership_tier=athlete.membership_tier,
        total_sessions=athlete.total_sessions,
        performance_rating=athlete.performance_rating,
        created_at=athlete.created_at,
    )


# Utility Functions
PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 100_000
PBKDF2_SALT_BYTES = 16


def get_password_hash(password: str) -> str:
    auth_service = AuthService(db=None)
    return auth_service.get_password_hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    auth_service = AuthService(db=None)
    return auth_service.create_access_token(data, expires_delta)


async def get_current_athlete(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Athlete:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    athlete = db.query(Athlete).filter(Athlete.username == token_data.username).first()
    if athlete is None:
        raise credentials_exception
    return athlete


# Refresh token helpers
from ..models.refresh_token import RefreshToken


def create_refresh_token(db: Session, athlete: Athlete, expires_days: int = 30) -> str:
    token = secrets.token_urlsafe(32)
    # Use HMAC with SECRET_KEY to avoid storing plain SHA256(token) (harder to precompute)
    token_hash = hmac.new(settings.SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
    expires_at = datetime.utcnow() + timedelta(days=expires_days)
    rt = RefreshToken(
        athlete_id=athlete.id, token_hash=token_hash, expires_at=expires_at, revoked=False
    )
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return token


def verify_refresh_token(db: Session, token: str) -> Optional[RefreshToken]:
    token_hash = hmac.new(settings.SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash, RefreshToken.revoked == False).first()
    if not rt:
        return None
    if rt.expires_at < datetime.utcnow():
        return None
    return rt


def revoke_refresh_token(db: Session, token: str) -> bool:
    token_hash = hmac.new(settings.SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if not rt:
        return False
    rt.revoked = True
    db.commit()
    return True


# Routes
@router.post("/signup", response_model=AthleteResponse, status_code=status.HTTP_201_CREATED)
async def signup(athlete_data: AthleteCreate, db: Session = Depends(get_db)):
    """Register a new athlete"""
    # Check if email already exists
    if db.query(Athlete).filter(Athlete.email == athlete_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    if db.query(Athlete).filter(Athlete.username == athlete_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Validate sport type
    if not is_valid_sport(athlete_data.sport_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sport_type"
        )
    
    # Create new athlete
    new_athlete = Athlete(
        email=athlete_data.email,
        username=athlete_data.username,
        hashed_password=get_password_hash(athlete_data.password),
        role="athlete",
        sport_type=athlete_data.sport_type,
        linked_sports=athlete_data.sport_type,
        skill_level=athlete_data.skill_level,
        dominant_hand=athlete_data.dominant_hand,
        height=athlete_data.height,
        weight=athlete_data.weight
    )
    
    db.add(new_athlete)
    db.commit()
    db.refresh(new_athlete)
    
    return athlete_to_response(new_athlete)


@router.post("/signup-coach", response_model=CoachResponse, status_code=status.HTTP_201_CREATED)
async def signup_coach(coach_data: CoachCreate, db: Session = Depends(get_db)):
    """Register a new coach"""
    # Check if email already exists
    if db.query(Athlete).filter(Athlete.email == coach_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    if db.query(Athlete).filter(Athlete.username == coach_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new coach
    new_coach = Athlete(
        email=coach_data.email,
        username=coach_data.username,
        hashed_password=get_password_hash(coach_data.password),
        role="coach",
        sport_type="boxing",  # Default, coaches can manage supported sports
        linked_sports="boxing,table_tennis,badminton"
    )
    
    db.add(new_coach)
    db.commit()
    db.refresh(new_coach)
    
    return CoachResponse(
        id=new_coach.id,
        email=new_coach.email,
        username=new_coach.username,
        role=new_coach.role,
        created_at=new_coach.created_at
    )


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    auth_service = AuthService(db)
    athlete = db.query(Athlete).filter(Athlete.username == form_data.username).first()
    
    if not athlete or not auth_service.verify_password(form_data.password, athlete.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not athlete.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = auth_service.create_access_token(
        data={"sub": athlete.username}, expires_delta=access_token_expires
    )

    refresh_token = auth_service.create_refresh_token(athlete)

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}


@router.post("/token/refresh")
async def refresh_with_token(
    request: RefreshRequest, db: Session = Depends(get_db)
):
    """Exchange a valid refresh token for a new access token (rotates refresh token)."""
    auth_service = AuthService(db)
    rt = auth_service.verify_refresh_token(request.refresh_token)
    if not rt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
        )

    athlete = db.query(Athlete).filter(Athlete.id == rt.athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token owner")

    auth_service.revoke_refresh_token(request.refresh_token)
    new_refresh = auth_service.create_refresh_token(athlete)

    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = auth_service.create_access_token(data={"sub": athlete.username}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": new_refresh}


@router.get("/me", response_model=AthleteResponse)
async def get_current_athlete_info(
    current_athlete: Athlete = Depends(get_current_athlete)
):
    """Get current authenticated athlete's information"""
    return athlete_to_response(current_athlete)


@router.put("/profile", response_model=AthleteResponse)
async def update_profile(
    profile_data: AthleteProfileUpdate,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    """Update athlete profile and linked sports"""
    if profile_data.linked_sports is not None:
        linked_sports = normalize_linked_sports(profile_data.linked_sports)
        if not linked_sports:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one sport must be linked"
            )
        current_athlete.linked_sports = ",".join(linked_sports)

    if profile_data.sport_type is not None:
        if not is_valid_sport(profile_data.sport_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid sport_type"
            )

        linked_sports = [sport for sport in (current_athlete.linked_sports or "").split(",") if sport]
        if linked_sports and profile_data.sport_type not in linked_sports:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Active sport must be one of linked sports"
            )

        current_athlete.sport_type = profile_data.sport_type

    if profile_data.skill_level is not None:
        current_athlete.skill_level = profile_data.skill_level

    if profile_data.dominant_hand is not None:
        current_athlete.dominant_hand = profile_data.dominant_hand

    if profile_data.height is not None:
        current_athlete.height = profile_data.height

    if profile_data.weight is not None:
        current_athlete.weight = profile_data.weight

    if profile_data.training_frequency_per_week is not None:
        current_athlete.training_frequency_per_week = profile_data.training_frequency_per_week

    db.commit()
    db.refresh(current_athlete)
    return athlete_to_response(current_athlete)


@router.post("/refresh", response_model=Token)
async def refresh_token(current_athlete: Athlete = Depends(get_current_athlete)):
    """Refresh access token"""
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": current_athlete.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


_GENERIC_RESET_RESPONSE = {"message": "If that email is registered, password reset instructions have been sent."}


@router.post("/password-reset/request")
async def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    """Always returns the same generic response regardless of whether the
    email is registered, to prevent account enumeration. Covered by the
    global IP-based RateLimitMiddleware already applied to every route."""
    athlete = db.query(Athlete).filter(Athlete.email == payload.email).first()
    if athlete:
        auth_service = AuthService(db)
        token = auth_service.create_password_reset_token(athlete)
        reset_link = f"{settings.FRONTEND_BASE_URL}/pages/reset-password.html?token={token}"
        try:
            send_password_reset_email(athlete.email, reset_link)
        except Exception:
            # A misconfigured/rejected SMTP send shouldn't surface as a
            # 500 or reveal to the caller whether the email exists - the
            # token still exists server-side, just log it for the admin
            # to notice and fix the SMTP_* env vars.
            logging.getLogger("pocketcoach.email").exception(
                "Failed to send password reset email to %s", athlete.email
            )

    return _GENERIC_RESET_RESPONSE


@router.post("/password-reset/confirm")
async def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    prt = auth_service.verify_password_reset_token(payload.token)
    if not prt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    if len(payload.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 characters")

    athlete = db.query(Athlete).filter(Athlete.id == prt.athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    athlete.hashed_password = get_password_hash(payload.new_password)
    auth_service.consume_password_reset_token(payload.token)

    # Force re-login everywhere - standard practice after a password change.
    db.query(RefreshToken).filter(RefreshToken.athlete_id == athlete.id, RefreshToken.revoked == False).update(
        {"revoked": True}
    )
    db.commit()

    return {"message": "Password has been reset. Please log in with your new password."}
