from typing import Dict

from .sports.table_tennis_analyzer import TableTennisAnalyzer
from .sports.boxing_analyzer import BoxingAnalyzer
from .sports.badminton_analyzer import BadmintonAnalyzer
from .sports.racket_analyzer import RacketAnalyzer
from .sports.tennis_analyzer import TennisAnalyzer
from .sports.combat_analyzer import CombatAnalyzer
from .sports.court_analyzer import CourtAnalyzer
from .sports.archery_analyzer import ArcheryAnalyzer
from .sports.fitness_analyzer import FitnessAnalyzer
from .sports.fencing_analyzer import FencingAnalyzer
from .sports.basketball_analyzer import BasketballAnalyzer
from .sports.ai_gym_coach_analyzer import AIGymCoachAnalyzer
from .sports.generic_fallback_analyzer import GenericFallbackAnalyzer


class UnregisteredSportError(ValueError):
    """A sport exists in sports_registry but has no analyzer mapped here at
    all (not even the fallback) - a safety net for a sport added to the
    registry without a corresponding factory entry."""


# Sports with a valid sports_registry entry but no tuned pose analyzer.
# Fabricating a score by borrowing an unrelated analyzer's checks (e.g.
# scoring kabaddi with boxing's guard-position logic) would look plausible
# but be meaningless, so these get the honest GenericFallbackAnalyzer
# instead. motogp/formula1 get a distinct reason since they're not
# pose-coachable in principle (seated/helmeted/vehicle-occluded), not just
# "not built yet".
NOT_YET_IMPLEMENTED = {
    "football", "baseball", "cricket", "gymnastics", "hockey", "ice_hockey",
    "kabaddi", "shooting", "swimming", "weight_lifting", "wwe",
}
NOT_POSE_COACHABLE = {"motogp", "formula1"}


class AnalyzerFactory:
    _registry: Dict[str, object] = {
        "table_tennis": TableTennisAnalyzer,
        "boxing": BoxingAnalyzer,
        "badminton": BadmintonAnalyzer,
        # Racket sports
        "tennis": TennisAnalyzer,
        "pickleball": lambda: RacketAnalyzer(sport_type="pickleball"),
        "squash": lambda: RacketAnalyzer(sport_type="squash"),
        # Combat sports
        "kickboxing": lambda: CombatAnalyzer(sport_type="kickboxing"),
        "muay_thai": lambda: CombatAnalyzer(sport_type="muay_thai"),
        "karate": lambda: CombatAnalyzer(sport_type="karate"),
        "taekwondo": lambda: CombatAnalyzer(sport_type="taekwondo"),
        "judo": lambda: CombatAnalyzer(sport_type="judo"),
        "bjj": lambda: CombatAnalyzer(sport_type="bjj"),
        "wrestling": lambda: CombatAnalyzer(sport_type="wrestling"),
        "fencing": FencingAnalyzer,
        # Court sports
        "basketball": BasketballAnalyzer,
        "volleyball": lambda: CourtAnalyzer(sport_type="volleyball"),
        "handball": lambda: CourtAnalyzer(sport_type="handball"),
        # Precision
        "indoor_archery": ArcheryAnalyzer,
        # Fitness & training
        "ai_gym_coach": lambda: AIGymCoachAnalyzer(sport_type="ai_gym_coach"),
        "stretching": lambda: FitnessAnalyzer(sport_type="stretching"),
        "mobility_training": lambda: FitnessAnalyzer(sport_type="mobility_training"),
        "rehabilitation": lambda: FitnessAnalyzer(sport_type="rehabilitation"),
        "home_workouts": lambda: FitnessAnalyzer(sport_type="home_workouts"),
        "calisthenics": lambda: FitnessAnalyzer(sport_type="calisthenics"),
    }

    @classmethod
    def _fallback(cls, sport_type: str):
        reason = "not_pose_coachable" if sport_type in NOT_POSE_COACHABLE else "not_yet_implemented"
        return GenericFallbackAnalyzer(sport_type=sport_type, reason=reason)

    @classmethod
    def get_analyzer(cls, sport_type: str):
        if sport_type in NOT_YET_IMPLEMENTED or sport_type in NOT_POSE_COACHABLE:
            return cls._fallback(sport_type)
        analyzer_factory = cls._registry.get(sport_type)
        if not analyzer_factory:
            raise UnregisteredSportError(f"No analyzer registered for sport type: {sport_type}")
        # registry entries are either analyzer classes or zero-arg lambdas -
        # both are directly callable to produce an instance.
        return analyzer_factory()

    @classmethod
    def register_analyzer(cls, sport_type: str, analyzer_cls):
        cls._registry[sport_type] = analyzer_cls
