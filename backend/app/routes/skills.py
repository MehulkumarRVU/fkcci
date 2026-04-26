from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.skill import Skill

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


@router.post("/", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(skill_data: SkillCreate, db: Session = Depends(get_db)):
    """Create a new skill (Admin function)"""
    # Check if skill name already exists
    existing_skill = db.query(Skill).filter(Skill.name == skill_data.name).first()
    if existing_skill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill with this name already exists"
        )
    
    # Validate sport type
    if skill_data.sport_type not in ["table_tennis", "boxing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sport_type must be 'table_tennis' or 'boxing'"
        )
    
    new_skill = Skill(**skill_data.dict())
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    
    return new_skill


@router.post("/seed")
async def seed_skills(db: Session = Depends(get_db)):
    """Seed the database with default skills"""
    # Check if skills already exist
    existing_skills = db.query(Skill).count()
    if existing_skills > 0:
        return {"message": f"Skills already seeded. Current count: {existing_skills}"}
    
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
    
    # Add all skills
    all_skills = table_tennis_skills + boxing_skills
    for skill_data in all_skills:
        skill = Skill(**skill_data)
        db.add(skill)
    
    db.commit()
    
    return {
        "message": "Skills seeded successfully",
        "table_tennis_skills": len(table_tennis_skills),
        "boxing_skills": len(boxing_skills),
        "total_skills": len(all_skills)
    }
