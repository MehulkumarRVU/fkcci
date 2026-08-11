-- Migration: add scoring_version, skill_name, joint_summary to sessions
-- scoring_version distinguishes pre-refactor ('v1') from post-refactor ('v2')
-- scores. skill_name/joint_summary give the profile-twin feature per-skill
-- and per-joint history to aggregate, which previously did not exist.
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
ALTER TABLE sessions ADD COLUMN scoring_version VARCHAR DEFAULT 'v1';
ALTER TABLE sessions ADD COLUMN skill_name VARCHAR;
ALTER TABLE sessions ADD COLUMN joint_summary TEXT;
COMMIT;
PRAGMA foreign_keys=ON;
