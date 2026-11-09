# Database Backup and Restore Report

Assessment date: 2026-11-08. PostgreSQL-native custom-format dumps are created
with `pg_dump`; restoration always targets a new, explicitly named database.
No restore operation overwrites the source database.

## Implemented workflow

- `scripts/backup_postgres.sh`: timestamped custom-format dump, `pg_restore
  --list` structural check, SHA-256 sidecar, restrictive file permissions,
  temporary-file cleanup, configurable retention, and JSON-line outcomes.
- `scripts/restore_postgres.sh`: requires the dump and checksum, validates both,
  refuses source-database targets and existing targets, restores with
  `pg_restore --exit-on-error`, checks tables and foreign keys, and removes only
  the target database it created if restore validation fails.
- `postgres-maintenance` Compose profile exposes one-shot backup/restore
  commands. `postgres-backup` runs the daily scheduled loop (default interval
  86,400 seconds) with automatic restart. Both are opt-in profiles.
- Backup storage is configurable with `BACKUP_STORAGE_PATH`, default retention
  is 30 days, and optional HTTPS-only failure notifications use
  `BACKUP_FAILURE_WEBHOOK_URL`.
- Credentials are passed through Compose environment variables; they are not
  embedded in scripts. Keep backup storage outside the repository and restrict
  it to the database/operations administrators.

## Operator commands

```powershell
# One-shot backup
docker compose --env-file .env up -d postgres
docker compose --env-file .env --profile maintenance run --rm postgres-maintenance /scripts/backup_postgres.sh

# Restore to a new disposable database (choose a unique, URL-safe name)
docker compose --env-file .env --profile maintenance run --rm `
  -e RESTORE_TARGET_DB=pocketcoach_restore_test `
  postgres-maintenance /scripts/restore_postgres.sh /backups/<timestamped-dump>.dump

# Optional scheduled backup service
docker compose --env-file .env --profile backup up -d postgres-backup
docker compose --env-file .env --profile backup logs --tail 100 postgres-backup
```

After restore, point a separate application instance at the restored database
and run the health check and read-only account/session verification. Never
change the normal application `DATABASE_URL` during a restore rehearsal.

## Recovery policy proposal

| Policy | Proposed value | Qualification |
|---|---|---|
| Frequency | Daily | The Compose scheduler runs immediately, then every 24 hours. Adjust interval to meet business needs. |
| Retention | 30 days | Configurable; align with privacy/data-retention policy and storage budget. |
| Recovery Point Objective | 24 hours | Best case for a daily schedule; actual RPO includes missed jobs and upload latency. |
| Recovery Time Objective | 4 hours | Planning target only; not a measured SLA. |
| Storage | Separate encrypted, access-controlled storage with off-host/off-site replication | Local bind-mounted files alone are not disaster recovery. |

## Validation evidence and limits

The current checksum-enforcing scripts completed a fresh dump and restore into
a separate PostgreSQL database. The restored database was reachable through
the application's SQLAlchemy/psycopg2 driver.

A second round trip used a synthetic athlete with an actual password hash, an
adaptive profile, and a completed Boxing session with historical score/joint
metadata. After restore, application password verification succeeded, the
adaptive profile was readable, and the historical session remained linked and
completed. The restored schema contained 12 foreign keys and 26 indexes.

A copy of a checksummed dump was modified by one byte. Restore rejected the
checksum before creating the target database; inspection confirmed the corrupt
target did not exist. This verifies checksum detection, not media durability
or off-host integrity.

The daily scheduler service and failure webhook were not started/tested.
No off-site copy, encryption-at-rest policy, production volume, or measured
RTO has been verified.

Backups passed local round-trip/integrity tests, but are **not production-safe**
until a protected off-host copy, scheduled execution, failure alerting, and a
restore drill on representative production-sized data are verified.
