-- Migration: add coach_notes table (coach<->athlete messaging)
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS coach_notes (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    session_id INTEGER,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY(athlete_id) REFERENCES athletes(id),
    FOREIGN KEY(author_id) REFERENCES athletes(id),
    FOREIGN KEY(session_id) REFERENCES sessions(id)
);
COMMIT;
PRAGMA foreign_keys=ON;
