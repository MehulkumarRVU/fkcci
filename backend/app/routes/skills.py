from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.athlete import Athlete
from ..models.skill import Skill
from ..models.skill_reference_pose import SkillReferencePose
from ..dependencies import require_role
from ..seed_data import seed_default_skills_if_empty
from .auth import get_current_athlete

router = APIRouter(prefix="/api/skills", tags=["Skills"])


# Pydantic Models
class SkillCreate(BaseModel):
    name: str
    sport_type: str
    description: Optional[str] = None
    technique_tips: Optional[str] = None
    common_mistakes: Optional[str] = None
    safety_warning: Optional[str] = None
    difficulty_level: Optional[str] = "beginner"
    primary_focus: Optional[str] = None


class SkillResponse(BaseModel):
    id: int
    name: str
    sport_type: str
    description: Optional[str]
    technique_tips: Optional[str]
    common_mistakes: Optional[str]
    safety_warning: Optional[str]
    difficulty_level: str
    primary_focus: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


# Routes
@router.get("/", response_model=List[SkillResponse])
async def get_skills(
    sport_type: Optional[str] = Query(None, description="Filter by sport type"),
    difficulty_level: Optional[str] = Query(None, description="Filter by difficulty"),
    db: Session = Depends(get_db)
):
    """Get all active skills, optionally filtered"""
    query = db.query(Skill).filter(Skill.is_active == True)
    
    if sport_type:
        query = query.filter(Skill.sport_type == sport_type)
    
    if difficulty_level:
        query = query.filter(Skill.difficulty_level == difficulty_level)
    
    skills = query.all()
    return skills


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(skill_id: int, db: Session = Depends(get_db)):
    """Get a specific skill by ID"""
    skill = db.query(Skill).filter(Skill.id == skill_id, Skill.is_active == True).first()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    return skill


@router.get("/{skill_id}/reference-pose")
async def get_skill_reference_pose(
    skill_id: int,
    skill_level: str = Query("beginner", description="beginner / intermediate / advanced"),
    db: Session = Depends(get_db)
):
    """Documented ideal-form joint-angle ranges for a skill (Digital Twin
    overlay). Live per-frame deviation classification doesn't read this
    table - it reuses the analyzer's own thresholds directly - this is the
    human-readable reference a coach UI can display."""
    reference = (
        db.query(SkillReferencePose)
        .filter(SkillReferencePose.skill_id == skill_id, SkillReferencePose.skill_level == skill_level)
        .first()
    )
    if not reference:
        raise HTTPException(status_code=404, detail="No reference pose available for this skill/level yet")

    return {
        "skill_id": reference.skill_id,
        "skill_level": reference.skill_level,
        "checkpoint_name": reference.checkpoint_name,
        "joint_angle_ranges": reference.joint_angle_ranges,
        "notes": reference.notes,
    }


@router.post("/", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("coach", "admin")),
):
    """Create a new skill (Admin function)"""
    # Check if skill name already exists
    existing_skill = db.query(Skill).filter(Skill.name == skill_data.name).first()
    if existing_skill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill with this name already exists"
        )
    
    # Validate sport type
    from ..sports_registry import is_valid_sport

    if not is_valid_sport(skill_data.sport_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sport_type"
        )
    
    new_skill = Skill(**skill_data.dict())
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    
    return new_skill


@router.post("/seed")
async def seed_skills(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db),
):
    """Seed the database with default skills.

    Requires a logged-in athlete/coach (not role-restricted) rather than
    being open to anyone - the frontend calls this automatically the first
    time a sport with no seeded skills is loaded (see session.js's
    loadSkills()), which normal athletes legitimately trigger, but it was
    previously reachable with no authentication at all."""
    result = seed_default_skills_if_empty(db)
    if result["already_seeded"]:
        return {"message": f"Skills already seeded. Current count: {result['existing_skills']}"}

    return {
        "message": "Added missing default skills",
        "added_skills": result["added_skills"],
        "existing_skills": result["existing_skills"],
        "generic_skills": result["generic_skills"]
    }

# Table Tennis Skills
    table_tennis_skills = [
        {
            "name": "Forehand Drive",
            "sport_type": "table_tennis",
            "description": "Basic forehand stroke with topspin",
            "technique_tips": "Start with weight on back foot, transfer forward. Keep elbow close to body. Follow through high.",
            "common_mistakes": "Elbow too far from body, insufficient weight transfer, not following through",
            "safety_warning": "Ensure proper warm-up to prevent shoulder strain",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Backhand Drive",
            "sport_type": "table_tennis",
            "description": "Basic backhand stroke with topspin",
            "technique_tips": "Rotate hips and shoulders. Contact ball in front of body. Smooth acceleration.",
            "common_mistakes": "Late contact, insufficient rotation, stiff wrist",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Topspin",
            "sport_type": "table_tennis",
            "description": "Advanced stroke adding heavy spin",
            "technique_tips": "Brush up on the ball. Fast racket acceleration. Low to high motion.",
            "common_mistakes": "Hitting through ball instead of brushing, timing issues",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Backspin",
            "sport_type": "table_tennis",
            "description": "Defensive stroke with underspin",
            "technique_tips": "Open racket angle. Brush down and forward. Soft touch.",
            "common_mistakes": "Too much force, incorrect angle, poor ball placement",
            "difficulty_level": "intermediate",
            "primary_focus": "defense"
        },
        {
            "name": "Serve Technique",
            "sport_type": "table_tennis",
            "description": "Ball toss and serve execution",
            "technique_tips": "Toss ball vertically at least 6 inches. Contact at peak. Vary spin and placement.",
            "common_mistakes": "Illegal toss, predictable serves, poor spin",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Side Shuffle Footwork",
            "sport_type": "table_tennis",
            "description": "Lateral movement technique",
            "technique_tips": "Stay on balls of feet. Small quick steps. Maintain ready position.",
            "common_mistakes": "Crossing feet, too slow, off balance",
            "difficulty_level": "beginner",
            "primary_focus": "speed"
        },
        {
            "name": "Smash",
            "sport_type": "table_tennis",
            "description": "Powerful finishing stroke",
            "technique_tips": "Get behind the ball. Full arm extension. Contact at highest point.",
            "common_mistakes": "Poor positioning, mistimed contact, lack of power",
            "difficulty_level": "advanced",
            "primary_focus": "power"
        }
    ]
    
    # Boxing Skills
    boxing_skills = [
        {
            "name": "Jab",
            "sport_type": "boxing",
            "description": "Quick straight punch with lead hand",
            "technique_tips": "Extend from shoulder. Rotate fist on impact. Keep other hand up. Snap back quickly.",
            "common_mistakes": "Dropping guard, no hip rotation, slow return",
            "safety_warning": "Always keep guard up to protect face",
            "difficulty_level": "beginner",
            "primary_focus": "speed"
        },
        {
            "name": "Cross",
            "sport_type": "boxing",
            "description": "Powerful straight punch with rear hand",
            "technique_tips": "Rotate hips and shoulders. Drive off back foot. Full extension. Chin down.",
            "common_mistakes": "Telegraphing punch, dropping rear hand, no rotation",
            "safety_warning": "Protect chin with shoulder on extension",
            "difficulty_level": "beginner",
            "primary_focus": "power"
        },
        {
            "name": "Hook",
            "sport_type": "boxing",
            "description": "Circular punch to head or body",
            "technique_tips": "Keep elbow at 90 degrees. Pivot on ball of foot. Rotate hips explosively.",
            "common_mistakes": "Wide elbow, no pivot, looping punch",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Uppercut",
            "sport_type": "boxing",
            "description": "Upward punch targeting chin",
            "technique_tips": "Slight knee bend. Drive upward with legs. Keep punch tight. Rotate shoulder.",
            "common_mistakes": "Dropping hands too low, overreaching, no leg drive",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Guard Position",
            "sport_type": "boxing",
            "description": "Defensive stance with hands up",
            "technique_tips": "Hands at chin level. Elbows tucked. Chin down. Eyes up.",
            "common_mistakes": "Hands too low, elbows flared, head up",
            "safety_warning": "Critical for protecting face and head",
            "difficulty_level": "beginner",
            "primary_focus": "defense"
        },
        {
            "name": "Slip & Roll",
            "sport_type": "boxing",
            "description": "Head movement to evade punches",
            "technique_tips": "Slight knee bend. Move head off centerline. Keep hands up. Return to center.",
            "common_mistakes": "Over-movement, dropping hands, predictable patterns",
            "difficulty_level": "intermediate",
            "primary_focus": "defense"
        },
        {
            "name": "Pivot Footwork",
            "sport_type": "boxing",
            "description": "Angular movement and positioning",
            "technique_tips": "Pivot on ball of lead foot. Step with rear foot. Maintain balance. Create angles.",
            "common_mistakes": "Flat-footed, crossing feet, losing balance",
            "difficulty_level": "advanced",
            "primary_focus": "speed"
        },
        {
            "name": "Combination Drills",
            "sport_type": "boxing",
            "description": "Multiple punch sequences",
            "technique_tips": "Flow between punches. Maintain rhythm. Keep guard up between punches.",
            "common_mistakes": "Windmilling, dropping hands, poor footwork",
            "difficulty_level": "advanced",
            "primary_focus": "accuracy"
        }
    ]

    # Badminton Skills
    badminton_skills = [
        {
            "name": "Serve Technique",
            "sport_type": "badminton",
            "description": "Correct racket preparation and toss for consistent serves",
            "technique_tips": "Use a relaxed grip, maintain a high wrist, and aim for precise contact.",
            "common_mistakes": "Tossing too low, swinging too hard, or failing to follow through.",
            "safety_warning": "Avoid overstraining the shoulder with excessive power.",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Clear",
            "sport_type": "badminton",
            "description": "Deep defensive shot to the backcourt",
            "technique_tips": "Swing the racket high and use wrist snap while rotating the body.",
            "common_mistakes": "Hitting too flat, poor timing, or insufficient follow-through.",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Smash",
            "sport_type": "badminton",
            "description": "Fast attacking shot directed downwards",
            "technique_tips": "Prepare with a high backswing, strike at the highest point, and follow through.",
            "common_mistakes": "Poor contact point, weak follow-through, or blocked wrist.",
            "difficulty_level": "advanced",
            "primary_focus": "power"
        },
        {
            "name": "Drop Shot",
            "sport_type": "badminton",
            "description": "Soft touch shot that falls just over the net",
            "technique_tips": "Use gentle wrist action and disguise the shot until the last moment.",
            "common_mistakes": "Hitting too hard or keeping the racket face open.",
            "difficulty_level": "intermediate",
            "primary_focus": "control"
        },
        {
            "name": "Net Play",
            "sport_type": "badminton",
            "description": "Tactical play close to the net",
            "technique_tips": "Stay low, keep the racket in front, and use soft touch.",
            "common_mistakes": "Backing away from the net or pushing the shuttle too hard.",
            "difficulty_level": "intermediate",
            "primary_focus": "precision"
        },
        {
            "name": "Split Step Footwork",
            "sport_type": "badminton",
            "description": "Ready movement before each shot",
            "technique_tips": "Jump lightly and be ready to move in any direction.",
            "common_mistakes": "Reacting late or staying flat-footed.",
            "difficulty_level": "beginner",
            "primary_focus": "speed"
        },
        {
            "name": "Defensive Block",
            "sport_type": "badminton",
            "description": "Controlled defensive strokes to return fast shots",
            "technique_tips": "Keep the racket face stable and absorb speed with a soft grip.",
            "common_mistakes": "Overpowering the shot or losing control.",
            "difficulty_level": "intermediate",
            "primary_focus": "defense"
        }
    ]
    
    # Add all skills
    all_skills = table_tennis_skills + boxing_skills + badminton_skills

    # Fallback generic skills for other supported sports
    seeded_sport_types = {skill_data["sport_type"] for skill_data in all_skills}
    generic_skills = []
    for sport_type, sport_info in SUPPORTED_SPORTS.items():
        if sport_type not in seeded_sport_types:
            generic_skills.append({
                "name": f"Basic {sport_info['name']} Technique",
                "sport_type": sport_type,
                "description": f"Fundamental {sport_info['name']} technique to build consistency and control.",
                "technique_tips": f"Focus on the core movement pattern for {sport_info['name']} and maintain steady form.",
                "common_mistakes": "Poor posture, inconsistent timing, and lack of focus on fundamentals.",
                "safety_warning": "Move slowly until form is stable and avoid overexertion.",
                "difficulty_level": "beginner",
                "primary_focus": "accuracy"
            })

    all_skills.extend(generic_skills)

    for skill_data in all_skills:
        skill = Skill(**skill_data)
        db.add(skill)
    
    db.commit()
    
    return {
        "message": "Skills seeded successfully",
        "table_tennis_skills": len(table_tennis_skills),
        "boxing_skills": len(boxing_skills),
        "badminton_skills": len(badminton_skills),
        "generic_skills": len(generic_skills),
        "total_skills": len(all_skills)
    }
