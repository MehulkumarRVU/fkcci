from datetime import datetime, timedelta
import base64
import hashlib
import hmac
import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.athlete import Athlete

try:
    import bcrypt
except ImportError:
    bcrypt = None

# Security Configuration
SECRET_KEY = "your-secret-key-change-in-production-use-env-variable"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# Pydantic Models
class AthleteCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    sport_type: str  # table_tennis or boxing
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
    sport_type: str
    linked_sports: List[str]
    skill_level: str
    dominant_hand: str
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


VALID_SPORTS = {"table_tennis", "boxing"}


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
        sport_type=athlete.sport_type,
        linked_sports=linked_sports,
        skill_level=athlete.skill_level,
        dominant_hand=athlete.dominant_hand,
        membership_tier=athlete.membership_tier,
        total_sessions=athlete.total_sessions,
        performance_rating=athlete.performance_rating,
        created_at=athlete.created_at,
    )


# Utility Functions
PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 100_000
PBKDF2_SALT_BYTES = 16


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if hashed_password.startswith("$2") and bcrypt is not None:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )

        scheme, iterations_str, salt_b64, stored_hash_b64 = hashed_password.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False

        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64.encode("utf-8"))
        stored_hash = base64.b64decode(stored_hash_b64.encode("utf-8"))

        computed_hash = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(computed_hash, stored_hash)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    salt = secrets.token_bytes(PBKDF2_SALT_BYTES)
    password_hash = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    hash_b64 = base64.b64encode(password_hash).decode("utf-8")
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_b64}${hash_b64}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_athlete(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Athlete:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
    if athlete_data.sport_type not in VALID_SPORTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sport_type must be 'table_tennis' or 'boxing'"
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
        sport_type="boxing",  # Default, coaches can manage both
        linked_sports="boxing,table_tennis"
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


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    athlete = db.query(Athlete).filter(Athlete.username == form_data.username).first()
    
    if not athlete or not verify_password(form_data.password, athlete.hashed_password):
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
    access_token = create_access_token(
        data={"sub": athlete.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


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
        if profile_data.sport_type not in VALID_SPORTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="sport_type must be 'table_tennis' or 'boxing'"
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
