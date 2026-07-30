from typing import Dict, List
from sqlalchemy.orm import Session

from .models.skill import Skill
from .sports_registry import SUPPORTED_SPORTS


def get_default_skill_data() -> List[Dict[str, str]]:
    ai_gym_skills = [
        {
            "name": "Squat Form",
            "sport_type": "ai_gym_coach",
            "description": "Fundamental squat technique from the Kaggle fitness exercise datasets for lower-body strength and mobility.",
            "technique_tips": "Keep feet shoulder-width apart, brace the core, and sit back while tracking knees over toes.",
            "common_mistakes": "Knees collapsing inward, excessive forward lean, or letting hips drop too low without control.",
            "safety_warning": "Use a comfortable range of motion and avoid forcing depth if mobility is limited.",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Push-Up Form",
            "sport_type": "ai_gym_coach",
            "description": "Classic push-up coaching cue based on common gym exercise datasets for chest, shoulders, and triceps.",
            "technique_tips": "Keep body in a straight line, lower with control, and press through the palms while maintaining shoulder stability.",
            "common_mistakes": "Sagging hips, flaring elbows too wide, or collapsing at the bottom of the rep.",
            "safety_warning": "Stop if shoulders or wrists feel strained and modify to an incline version if needed.",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Deadlift Form",
            "sport_type": "ai_gym_coach",
            "description": "Hip-hinge movement pattern inspired by fitness program datasets for posterior-chain strength.",
            "technique_tips": "Brace your core, hinge at the hips, and keep the bar close to the body while maintaining a neutral spine.",
            "common_mistakes": "Rounded back, jerking the weight, or lifting with the arms instead of the hips.",
            "safety_warning": "Start with light load and prioritize form before adding weight.",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Lunge Technique",
            "sport_type": "ai_gym_coach",
            "description": "Split-stance lower-body exercise from fitness workout datasets for balance, mobility, and leg strength.",
            "technique_tips": "Step into a long stride, keep the torso upright, and drive through the front heel to stand tall.",
            "common_mistakes": "Forward knee collapsing inward, overstriding, or losing balance.",
            "safety_warning": "Use a controlled range of motion and keep the front knee aligned over the foot.",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Plank Stability",
            "sport_type": "ai_gym_coach",
            "description": "Core stability drill inspired by general fitness exercise datasets for posture and bracing.",
            "technique_tips": "Keep the body straight, engage the glutes, and avoid letting the hips sag or pike up.",
            "common_mistakes": "Dropping the hips, arching the lower back, or holding the breath.",
            "safety_warning": "Stop if lower-back discomfort becomes sharp or persistent.",
            "difficulty_level": "beginner",
            "primary_focus": "defense"
        },
        {
            "name": "Bent-Over Row",
            "sport_type": "ai_gym_coach",
            "description": "Upper-back pulling movement from workout-program datasets for posture and pulling strength.",
            "technique_tips": "Hinge at the hips, keep the spine neutral, and pull the elbows back without shrugging the shoulders.",
            "common_mistakes": "Rounded back, yanking the weight, or using momentum instead of the back muscles.",
            "safety_warning": "Start with a manageable load and stop if the lower back feels strained.",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Shoulder Press",
            "sport_type": "ai_gym_coach",
            "description": "Overhead pressing movement for shoulder strength and stability from fitness exercise catalogs.",
            "technique_tips": "Brace the ribs, press vertically, and keep the wrists stacked over the elbows.",
            "common_mistakes": "Arching the lower back, leaning too far back, or letting the head jut forward.",
            "safety_warning": "Avoid locking the elbows aggressively and maintain smooth control.",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Burpee",
            "sport_type": "ai_gym_coach",
            "description": "Full-body conditioning movement from workout datasets for strength, coordination, and endurance.",
            "technique_tips": "Move with rhythm, keep the chest proud, and land softly during the squat thrust.",
            "common_mistakes": "Rushing the movement, collapsing at the bottom, or losing posture.",
            "safety_warning": "Reduce speed if your knees or wrists feel stressed.",
            "difficulty_level": "intermediate",
            "primary_focus": "speed"
        },
        {
            "name": "Glute Bridge",
            "sport_type": "ai_gym_coach",
            "description": "Posterior-chain activation drill for hip extension and core control from fitness routines.",
            "technique_tips": "Drive through the heels, keep the ribs down, and pause briefly at the top of the rep.",
            "common_mistakes": "Overarching the lower back or pushing with the feet too aggressively.",
            "safety_warning": "Keep the movement controlled and avoid forcing an excessive range.",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Pull-Up Form",
            "sport_type": "ai_gym_coach",
            "description": "Vertical pulling exercise widely used in strength-training programs for back and biceps development.",
            "technique_tips": "Start from a dead hang, pull the elbows down, and avoid swinging the body.",
            "common_mistakes": "Kipping the body, shrugging the shoulders, or failing to engage the lats.",
            "safety_warning": "Use an assisted variation if full reps are not yet possible.",
            "difficulty_level": "advanced",
            "primary_focus": "power"
        },
        {
            "name": "Dips Technique",
            "sport_type": "ai_gym_coach",
            "description": "Upper-body pressing movement from training plans for chest, shoulders, and triceps.",
            "technique_tips": "Lower with control, keep the elbows slightly tucked, and press back up without collapsing at the shoulders.",
            "common_mistakes": "Dropping too deep, flaring the elbows, or leaning excessively forward.",
            "safety_warning": "Stop if shoulders feel pinched or unstable.",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Mountain Climbers",
            "sport_type": "ai_gym_coach",
            "description": "Dynamic conditioning drill from fitness datasets for core endurance and cardio.",
            "technique_tips": "Keep a strong plank position, move the knees quickly, and maintain rhythm.",
            "common_mistakes": "Hips bouncing too high, losing alignment, or rushing without control.",
            "safety_warning": "Keep the movement steady and avoid hard impact on the wrists.",
            "difficulty_level": "intermediate",
            "primary_focus": "speed"
        },
        {
            "name": "Bench Press",
            "sport_type": "ai_gym_coach",
            "description": "Classic upper-push barbell press for chest, shoulders, and triceps strength.",
            "technique_tips": "Keep the shoulders pinned back, feet planted, and lower the bar with control to the chest.",
            "common_mistakes": "Flared elbows, bouncing the bar, or lifting the hips off the bench.",
            "safety_warning": "Use a spotter for heavy loads and avoid overextending the shoulders.",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Incline Bench Press",
            "sport_type": "ai_gym_coach",
            "description": "Angled upper-push press that emphasizes the upper chest and front delts.",
            "technique_tips": "Set the bench to a moderate incline, keep the wrists stacked, and press smoothly.",
            "common_mistakes": "Too steep an angle, excessive shoulder shrugging, or poor path of motion.",
            "safety_warning": "Avoid forcing range if the shoulder feels compressed.",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Decline Bench Press",
            "sport_type": "ai_gym_coach",
            "description": "Downward-angled press that shifts emphasis toward the lower chest and triceps.",
            "technique_tips": "Brace the torso, lower under control, and keep the elbows slightly tucked.",
            "common_mistakes": "Arching too hard, flaring the elbows, or rushing the eccentric.",
            "safety_warning": "Only use decline bench equipment that is stable and secure.",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Tricep Pushdown",
            "sport_type": "ai_gym_coach",
            "description": "Cable-based isolation exercise focused on triceps endurance and strength.",
            "technique_tips": "Keep the elbows pinned to the sides, move through a full range, and avoid swinging.",
            "common_mistakes": "Leaning forward, using momentum, or letting the shoulders shrug.",
            "safety_warning": "Stop if the elbows or wrists feel irritated.",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Lat Pulldown",
            "sport_type": "ai_gym_coach",
            "description": "Machine-based upper-pull movement for the lats, upper back, and biceps.",
            "technique_tips": "Pull the bar to the upper chest, keep the torso stable, and avoid leaning back excessively.",
            "common_mistakes": "Yanking the bar, using momentum, or shrugging the shoulders.",
            "safety_warning": "Use a comfortable weight and keep the motion smooth.",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Barbell Biceps Curl",
            "sport_type": "ai_gym_coach",
            "description": "Classic upper-pull exercise for biceps strength and arm development.",
            "technique_tips": "Keep the elbows near the ribs, curl without swinging, and control the lowering phase.",
            "common_mistakes": "Swinging the torso, using momentum, or over-arching the back.",
            "safety_warning": "Choose a weight that allows strict form.",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Hammer Curl",
            "sport_type": "ai_gym_coach",
            "description": "Neutral-grip curl emphasizing the biceps and brachialis with strong forearm involvement.",
            "technique_tips": "Keep the wrists neutral, curl through the full range, and avoid rocking the body.",
            "common_mistakes": "Twisting the wrists, swinging the weight, or losing elbow position.",
            "safety_warning": "Use a controlled load to protect the elbows and wrists.",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "T-Bar Row",
            "sport_type": "ai_gym_coach",
            "description": "Upper-back pulling movement for lats, rhomboids, and posterior shoulder strength.",
            "technique_tips": "Set the chest proud, pull the handle to the lower ribs, and avoid rounding the back.",
            "common_mistakes": "Jerking the weight, excessive torso swing, or shrugging the shoulders.",
            "safety_warning": "Keep the spine neutral and stop if the lower back feels strained.",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Chest Fly Machine",
            "sport_type": "ai_gym_coach",
            "description": "Isolation movement for chest muscle development with a controlled stretch and contraction.",
            "technique_tips": "Keep a slight bend in the elbows, open the arms smoothly, and squeeze the chest at the top.",
            "common_mistakes": "Overstretching the shoulders, letting the elbows lock, or using momentum.",
            "safety_warning": "Stop if the shoulders feel pinched at the end range.",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Romanian Deadlift",
            "sport_type": "ai_gym_coach",
            "description": "Hip-hinge lower-body movement focused on hamstrings, glutes, and posture.",
            "technique_tips": "Keep the knees soft, hinge at the hips, and feel the stretch through the hamstrings.",
            "common_mistakes": "Rounded back, pushing with the arms, or bending the knees too aggressively.",
            "safety_warning": "Start with light weight and keep the spine neutral.",
            "difficulty_level": "intermediate",
            "primary_focus": "power"
        },
        {
            "name": "Hip Thrust",
            "sport_type": "ai_gym_coach",
            "description": "Glute-focused lower-body exercise emphasizing hip extension and posterior chain power.",
            "technique_tips": "Brace the core, drive through the heels, and pause at the top of the movement.",
            "common_mistakes": "Over-arching the lower back or losing tension in the glutes.",
            "safety_warning": "Use a stable bench and avoid excessive spinal extension.",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Leg Extension",
            "sport_type": "ai_gym_coach",
            "description": "Machine-based lower-body isolation exercise for the quadriceps.",
            "technique_tips": "Keep the hips pinned and extend the knees smoothly without swinging.",
            "common_mistakes": "Using momentum, arching the back, or letting the knees roll inward.",
            "safety_warning": "Use a manageable load and avoid forcing the knees past comfort.",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Leg Raises",
            "sport_type": "ai_gym_coach",
            "description": "Lower-body and hip-flexor movement that helps strengthen the abs and improve control.",
            "technique_tips": "Keep the lower back pressed down and raise the legs with control.",
            "common_mistakes": "Arching the back, swinging the legs, or using momentum.",
            "safety_warning": "Move slowly and stop if the lower back feels strained.",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        },
        {
            "name": "Plank",
            "sport_type": "ai_gym_coach",
            "description": "Isometric core exercise focused on abdominal stiffness, posture, and stability.",
            "technique_tips": "Keep the body in a straight line, brace the abs, and breathe steadily.",
            "common_mistakes": "Sagging hips, piking the butt up, or holding the breath.",
            "safety_warning": "Stop if the lower back feels sharp or compressed.",
            "difficulty_level": "beginner",
            "primary_focus": "defense"
        },
        {
            "name": "Russian Twist",
            "sport_type": "ai_gym_coach",
            "description": "Rotational core movement for obliques, abs, and trunk control.",
            "technique_tips": "Keep the torso tall, rotate through the ribcage, and move with control.",
            "common_mistakes": "Twisting too fast, rounding the back, or using the arms instead of the core.",
            "safety_warning": "Avoid forcing the range if the lower back feels stressed.",
            "difficulty_level": "beginner",
            "primary_focus": "accuracy"
        }
    ]

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

    return ai_gym_skills + table_tennis_skills + boxing_skills + badminton_skills


def seed_default_skills_if_empty(db: Session) -> Dict[str, int]:
    existing_skill_names = {name for (name,) in db.query(Skill.name).all()}
    existing_skills_count = len(existing_skill_names)

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

    added_skill_count = 0
    for skill_data in skills:
        if skill_data["name"] in existing_skill_names:
            continue
        db.add(Skill(**skill_data))
        added_skill_count += 1

    if added_skill_count > 0:
        db.commit()

    return {
        "already_seeded": added_skill_count == 0,
        "existing_skills": existing_skills_count,
        "added_skills": added_skill_count,
        "generic_skills": len(generic_skills)
    }
