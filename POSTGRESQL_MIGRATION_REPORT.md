# PostgreSQL Migration and Upgrade Report

Assessment date: 2026-11-08. Scope: repository schema-management code and a
synthetic PostgreSQL upgrade database. The retained `pocketcoach-check`
database was not used as a migration target.

## Schema-management inventory

- Ten SQLAlchemy models are registered by `init_database()`.
- Startup calls `Base.metadata.create_all()`, adds known compatibility
  columns, backfills `athletes.linked_sports`, then seeds skills and reference
  poses.
- The compatibility migration now runs at startup for both SQLite and
  PostgreSQL. PostgreSQL also validates legacy coach/session foreign keys and
  creates the coach/session lookup indexes when absent.
- `backend/migrations/` contains SQL files `0002` through `0008`; there is no
  `0001` or Alembic configuration/version chain.
- Those SQL files use SQLite `PRAGMA` syntax. `app/migrate.py` naïvely splits
  on semicolons, records filenames, and is not called by application startup.
  Treat these files as legacy SQLite migration history, not as the supported
  PostgreSQL upgrade mechanism.

## Validation performed

An isolated PostgreSQL 16 database was built with a representative pre-adaptive
`athletes` and `sessions` schema plus one synthetic athlete and completed
session. Running application initialization preserved the account and
historical score/session relationship, backfilled `linked_sports`, added the
expected adaptive, scoring, and timestamp columns, and completed default data
seeding. The legacy coach and session foreign keys and two lookup indexes were
also verified.

A failure/rollback rehearsal held an exclusive lock on the legacy `sessions`
table while setting a 150 ms lock timeout. The upgrade added some columns to
`athletes`, then failed on the locked table. PostgreSQL rolled back the
transaction: inspection found none of those partial columns. Releasing the
lock and retrying completed the migration, validating constraints and
indexes. No destructive operation targeted the retained validation database.

The fresh Compose database was initialized twice. The inspected schema had
10 tables, 12 foreign keys, and 26 indexes. Exact table/data counts and the
backup/restore round-trip evidence are in `DATABASE_BACKUP_RESTORE_REPORT.md`.

## Recovery and compatibility risks

- The compatibility path is additive and idempotent for the exercised
  schemas; no data columns or user rows were deleted.
- DDL changes occur in transactions where supported by PostgreSQL, but
  `create_all()` and the subsequent compatibility transaction are not one
  atomic migration unit.
- The legacy SQL migration runner is not portable to PostgreSQL and can fail
  on an already partially applied migration. Do not run it against production
  PostgreSQL.
- A production upgrade still requires a sanitized, representative schema/data
  copy, a pre-upgrade backup, review of all constraints/indexes, and a
  maintenance-window rollback rehearsal.
- `init_database()` spans `create_all()` and the compatibility transaction,
  so table creation is not atomic with the additive column/constraint phase.
  The tested rollback covers the compatibility transaction only.

## Release status

**PARTIAL.** Fresh initialization, synthetic prior-schema upgrade, and
compatibility-transaction failure/retry pass. Formal versioned PostgreSQL
migrations and production-data compatibility remain deployment gates.
