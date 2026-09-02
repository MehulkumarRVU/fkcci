import sys
import os
from datetime import date, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.services.gamification_service import update_streak, check_and_award_achievements, ACHIEVEMENTS


class DummyAthlete:
    def __init__(self, **kwargs):
        self.id = 1
        self.current_streak = 0
        self.longest_streak = 0
        self.last_session_date = None
        self.total_sessions = 0
        self.linked_sports = ""
        for k, v in kwargs.items():
            setattr(self, k, v)


class DummySession:
    def __init__(self, performance_score=0.0):
        self.performance_score = performance_score


def test_streak_increments_on_consecutive_days():
    athlete = DummyAthlete()
    day1 = date(2026, 1, 1)
    update_streak(athlete, day1)
    assert athlete.current_streak == 1
    assert athlete.longest_streak == 1

    day2 = day1 + timedelta(days=1)
    update_streak(athlete, day2)
    assert athlete.current_streak == 2
    assert athlete.longest_streak == 2


def test_streak_same_day_does_not_change():
    athlete = DummyAthlete(current_streak=3, longest_streak=3, last_session_date=date(2026, 1, 1))
    update_streak(athlete, date(2026, 1, 1))
    assert athlete.current_streak == 3


def test_streak_resets_after_gap():
    athlete = DummyAthlete(current_streak=5, longest_streak=5, last_session_date=date(2026, 1, 1))
    update_streak(athlete, date(2026, 1, 5))  # 4-day gap
    assert athlete.current_streak == 1
    assert athlete.longest_streak == 5  # longest_streak preserved, not reset


def test_streak_longest_tracks_new_peak():
    athlete = DummyAthlete(current_streak=2, longest_streak=2, last_session_date=date(2026, 1, 1))
    update_streak(athlete, date(2026, 1, 2))
    assert athlete.current_streak == 3
    assert athlete.longest_streak == 3


class DummyQuery:
    def __init__(self, rows):
        self._rows = rows

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.added = []

    def query(self, model):
        return DummyQuery(self.added)

    def add(self, obj):
        self.added.append(obj)


def test_achievement_awarded_for_first_session():
    athlete = DummyAthlete(total_sessions=1)
    db = DummyDB()
    newly = check_and_award_achievements(athlete, db, DummySession(performance_score=50))
    assert "first_session" in newly
    assert len(db.added) == 1


def test_achievement_not_double_awarded():
    athlete = DummyAthlete(total_sessions=1)
    db = DummyDB()
    first = check_and_award_achievements(athlete, db, DummySession(performance_score=50))
    assert "first_session" in first

    # db.added now holds the real AthleteAchievement rows just inserted (as
    # DummyDB.query()/DummyQuery.all() would see on a second real call).
    second = check_and_award_achievements(athlete, db, DummySession(performance_score=50))
    assert "first_session" not in second


def test_high_score_achievement():
    athlete = DummyAthlete(total_sessions=1)
    db = DummyDB()
    newly = check_and_award_achievements(athlete, db, DummySession(performance_score=97))
    assert "high_score" in newly


def test_no_high_score_achievement_below_threshold():
    athlete = DummyAthlete(total_sessions=1)
    db = DummyDB()
    newly = check_and_award_achievements(athlete, db, DummySession(performance_score=80))
    assert "high_score" not in newly


def test_multi_sport_achievement():
    athlete = DummyAthlete(total_sessions=1, linked_sports="boxing,table_tennis,badminton")
    db = DummyDB()
    newly = check_and_award_achievements(athlete, db, DummySession(performance_score=50))
    assert "multi_sport" in newly


def test_all_achievement_codes_have_definitions():
    athlete = DummyAthlete(total_sessions=50, current_streak=30, linked_sports="a,b,c")
    db = DummyDB()
    newly = check_and_award_achievements(athlete, db, DummySession(performance_score=99))
    for code in newly:
        assert code in ACHIEVEMENTS
        assert "name" in ACHIEVEMENTS[code]
        assert "icon" in ACHIEVEMENTS[code]
