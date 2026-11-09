# Deployment Guide

## Current validation status

The Docker Compose configuration and image were validated locally. A complete
stack with backend, PostgreSQL, Redis, and Nginx reached healthy status.
PostgreSQL schema initialization, repeat initialization, persistence across
database/backend restarts, Redis connectivity, and Nginx API routing passed.
The isolated validation stack is available at `http://127.0.0.1:18001` for
this workspace. These checks do not certify a production deployment.

See `DEPLOYMENT_REPORT.md` for measured outcomes and remaining blockers.
See `PRODUCTION_READINESS_CHECKLIST.md` before authorizing an external pilot or
public launch.

## Configure and run

1. Copy `.env.example` to `.env`.
2. Set a unique high-entropy secret and strong URL-safe PostgreSQL credentials.
   Configure production CORS origins, `ENV=production`, SMTP host/from-address,
   paired SMTP credentials if authentication is used, and the public HTTPS
   `FRONTEND_BASE_URL`.
3. Validate interpolation and configuration:

   ```powershell
   docker compose config --quiet
   ```

4. Build and start:

   ```powershell
   docker compose up --build -d
   docker compose ps
   docker compose logs --tail 100 backend postgres redis nginx
   ```

5. To use the TLS override, first provision `fullchain.pem` and `privkey.pem`
   outside the repository and set `TLS_CERTIFICATE_PATH` to their directory:

   ```powershell
   docker compose --env-file .env -f docker-compose.yml -f docker-compose.tls.yml config --quiet
   docker compose --env-file .env -f docker-compose.yml -f docker-compose.tls.yml up --build -d
   ```

6. Verify the API and frontend through the intended public endpoint. Then
   verify authentication, camera access over HTTPS, and database persistence
   across a controlled container restart.

7. Configure a separate, access-controlled backup path and start the opt-in
   daily service:

   ```powershell
   docker compose --env-file .env --profile backup up -d postgres-backup
   ```

   Inspect its logs and complete a restore into a new database before enabling
   athlete access. See `DATABASE_BACKUP_RESTORE_REPORT.md`.

The Compose file defines backend, PostgreSQL, Redis, and Nginx services, a
named PostgreSQL data volume, health checks, and service readiness
dependencies. The backend is not published directly to the host; Nginx is the
public entry point.

## Release blockers and safeguards

- Validate an upgrade from representative existing PostgreSQL data before
  production; this run tested a fresh database and repeat initialization.
- Configure and verify real SMTP delivery.
- Use TLS, narrowly scoped CORS, secret management, backups with a restore
  test, monitoring, log retention, and restricted network access.
- The health endpoint confirms application responsiveness; it is not a
  complete diagnostic. Use `/health/ready` for PostgreSQL and Redis readiness.
- Redis failure degrades rate limiting to per-process memory buckets.
- Run device/camera checks on supported browsers and perform an independent
  deployment security review before release.
- Compose TLS configuration has not been tested with a real certificate.
- Production readiness remains **PARTIAL**; do not publicly launch on the
  strength of local container health alone.

## Operational reports

- `PRODUCTION_READINESS_CHECKLIST.md`
- `POSTGRESQL_MIGRATION_REPORT.md`
- `DATABASE_BACKUP_RESTORE_REPORT.md`
- `PRODUCTION_CONFIGURATION_REPORT.md`
- `MONITORING_AND_ALERTING_REPORT.md`
- `INDEPENDENT_SECURITY_REVIEW_PACKAGE.md`
- `AUTHENTICATED_LOAD_TEST_REPORT.md`
- `PHYSICAL_DEVICE_VALIDATION_REPORT.md`
- `CONTROLLED_ATHLETE_PILOT_PLAN.md`
