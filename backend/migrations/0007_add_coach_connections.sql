-- Migration: add coach_connection_requests and coach_invites tables
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS coach_connection_requests (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL,
    coach_id INTEGER NOT NULL,
    status VARCHAR DEFAULT 'pending',
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    responded_at DATETIME,
    FOREIGN KEY(athlete_id) REFERENCES athletes(id),
    FOREIGN KEY(coach_id) REFERENCES athletes(id)
);
CREATE TABLE IF NOT EXISTS coach_invites (
    id INTEGER PRIMARY KEY,
    coach_id INTEGER NOT NULL,
    code VARCHAR NOT NULL UNIQUE,
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    revoked BOOLEAN DEFAULT 0,
    FOREIGN KEY(coach_id) REFERENCES athletes(id)
);
COMMIT;
PRAGMA foreign_keys=ON;
