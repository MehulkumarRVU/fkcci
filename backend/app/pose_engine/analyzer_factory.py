
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
    def get_analyzer(cls, sport_type: str):
        analyzer_factory = cls._registry.get(sport_type)
        if not analyzer_factory:
            raise ValueError(f"No analyzer registered for sport type: {sport_type}")
        # registry entries can be classes or callables returning instances
        if callable(analyzer_factory):
            return analyzer_factory() if not isinstance(analyzer_factory, type) else analyzer_factory()
        return analyzer_factory

    @classmethod
    def register_analyzer(cls, sport_type: str, analyzer_cls):
        cls._registry[sport_type] = analyzer_cls
