from typing import Dict, List
from sqlalchemy.orm import Session

from .models.skill import Skill
from .sports_registry import SUPPORTED_SPORTS


def get_default_skill_data() -> List[Dict[str, str]]:
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
            "safety_warning": "Ensure proper warm-up to prevent shoulder strain",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Topspin",
            "sport_type": "table_tennis",
            "description": "Advanced stroke adding heavy spin",
            "technique_tips": "Brush up on the ball. Fast racket acceleration. Low to high motion.",
            "common_mistakes": "Hitting through ball instead of brushing, timing issues",
            "safety_warning": "Warm up wrist and shoulder before practice",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Backspin",
            "sport_type": "table_tennis",
            "description": "Defensive stroke with underspin",
            "technique_tips": "Open racket angle. Brush down and forward. Soft touch.",
            "common_mistakes": "Too much force, incorrect angle, poor ball placement",
            "safety_warning": "Avoid overstraining the wrist",
            "difficulty_level": "intermediate",
            "primary_focus": "defense"
        },
        {
            "name": "Serve Technique",
            "sport_type": "table_tennis",
            "description": "Ball toss and serve execution",
            "technique_tips": "Toss ball vertically at least 6 inches. Contact at peak. Vary spin and placement.",
            "common_mistakes": "Illegal toss, predictable serves, poor spin",
            "safety_warning": "Practice legal serves and keep the motion controlled",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Side Shuffle Footwork",
            "sport_type": "table_tennis",
            "description": "Lateral movement technique",
            "technique_tips": "Stay on balls of feet. Small quick steps. Maintain ready position.",
            "common_mistakes": "Crossing feet, too slow, off balance",
            "safety_warning": "Keep movements smooth to prevent ankle twisting",
            "difficulty_level": "beginner",
            "primary_focus": "speed"
        },
        {
            "name": "Table Tennis Smash",
            "sport_type": "table_tennis",
            "description": "Powerful finishing stroke",
            "technique_tips": "Get behind the ball. Full arm extension. Contact at highest point.",
            "common_mistakes": "Poor positioning, mistimed contact, lack of power",
            "safety_warning": "Avoid overexerting the wrist and shoulder",
            "difficulty_level": "advanced",
            "primary_focus": "power"
        }
    ]

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
            "safety_warning": "Maintain balance and keep guard high",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Uppercut",
            "sport_type": "boxing",
            "description": "Upward punch targeting chin",
            "technique_tips": "Slight knee bend. Drive upward with legs. Keep punch tight. Rotate shoulder.",
            "common_mistakes": "Dropping hands too low, overreaching, no leg drive",
            "safety_warning": "Protect the head and keep elbows close to the body",
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
            "safety_warning": "Move safely and avoid overcommitting",
            "difficulty_level": "intermediate",
            "primary_focus": "defense"
        },
        {
            "name": "Pivot Footwork",
            "sport_type": "boxing",
            "description": "Angular movement and positioning",
            "technique_tips": "Pivot on ball of lead foot. Step with rear foot. Maintain balance. Create angles.",
            "common_mistakes": "Flat-footed, crossing feet, losing balance",
            "safety_warning": "Avoid twisting the knee while pivoting",
            "difficulty_level": "advanced",
            "primary_focus": "speed"
        }
    ]

    badminton_skills = [
        {
            "name": "Badminton Serve Technique",
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
            "safety_warning": "Keep the motion controlled to prevent shoulder strain.",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Badminton Smash",
            "sport_type": "badminton",
            "description": "Fast attacking shot directed downwards",
            "technique_tips": "Prepare with a high backswing, strike at the highest point, and follow through.",
            "common_mistakes": "Poor contact point, weak follow-through, or blocked wrist.",
            "safety_warning": "Avoid hyperextending the elbow.",
            "difficulty_level": "advanced",
            "primary_focus": "power"
        },
        {
            "name": "Drop Shot",
            "sport_type": "badminton",
            "description": "Soft touch shot that falls just over the net",
            "technique_tips": "Use gentle wrist action and disguise the shot until the last moment.",
            "common_mistakes": "Hitting too hard or keeping the racket face open.",
            "safety_warning": "Keep movements smooth to avoid wrist strain.",
            "difficulty_level": "intermediate",
            "primary_focus": "control"
        },
        {
            "name": "Net Play",
            "sport_type": "badminton",
            "description": "Tactical play close to the net",
            "technique_tips": "Stay low, keep the racket in front, and use soft touch.",
            "common_mistakes": "Backing away from the net or pushing the shuttle too hard.",
            "safety_warning": "Avoid overreaching and losing balance.",
            "difficulty_level": "intermediate",
            "primary_focus": "precision"
        },
        {
            "name": "Split Step Footwork",
            "sport_type": "badminton",
            "description": "Ready movement before each shot",
            "technique_tips": "Jump lightly and be ready to move in any direction.",
            "common_mistakes": "Reacting late or staying flat-footed.",
            "safety_warning": "Do not land heavily on the knees.",
            "difficulty_level": "beginner",
            "primary_focus": "speed"
        }
    ]

    return table_tennis_skills + boxing_skills + badminton_skills


def seed_default_skills_if_empty(db: Session) -> Dict[str, int]:
    existing_skills = db.query(Skill).count()
    if existing_skills > 0:
        return {"already_seeded": True, "count": existing_skills}

    skills = get_default_skill_data()
    seeded_sports = {skill["sport_type"] for skill in skills}

    generic_skills = []
    for sport_type, sport_info in SUPPORTED_SPORTS.items():
        if sport_type not in seeded_sports:
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

    skills.extend(generic_skills)

    for skill_data in skills:
        skill = Skill(**skill_data)
        db.add(skill)

    db.commit()

    return {
        "already_seeded": False,
        "seeded_count": len(skills),
        "generic_skills": len(generic_skills)
    }
