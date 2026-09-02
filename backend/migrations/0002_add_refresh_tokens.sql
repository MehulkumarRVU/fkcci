-- Migration: add refresh_tokens table
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL,
    token_hash VARCHAR NOT NULL UNIQUE,
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    expires_at DATETIME NOT NULL,
    revoked BOOLEAN DEFAULT 0,
    FOREIGN KEY(athlete_id) REFERENCES athletes(id)
);
COMMIT;
PRAGMA foreign_keys=ON;
