-- Migration: add gamification (streaks + achievements)
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
ALTER TABLE athletes ADD COLUMN current_streak INTEGER DEFAULT 0;
ALTER TABLE athletes ADD COLUMN longest_streak INTEGER DEFAULT 0;
ALTER TABLE athletes ADD COLUMN last_session_date DATE;
CREATE TABLE IF NOT EXISTS athlete_achievements (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL,
    code VARCHAR NOT NULL,
    earned_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY(athlete_id) REFERENCES athletes(id)
);
COMMIT;
PRAGMA foreign_keys=ON;
