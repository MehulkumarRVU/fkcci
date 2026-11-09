# Testing and Runtime Report

Assessment date: 2026-11-09. Checks were run locally in this workspace; they
are not a release certification.

## Passed

- Backend regression suite: **118 passed, 0 skipped**, with
  `TEST_REDIS_URL=redis://127.0.0.1:16379/0` against a separate Redis 8 test
  instance. The suite was rerun after the authentication and execution-boundary
  changes.
- Python bytecode compilation:
  `python -m compileall -q backend/app backend/tests`.
- Dependency consistency: `python -m pip check` reported no broken requirements
  in the latest isolated image.
- Frontend JavaScript syntax: `node --check` passed for all 19 JavaScript files.
- Base and performance Docker Compose configurations validated;
  `git diff --check` passed.
- Fresh backend images were built under separate verification tags. The
  latest image passed PostgreSQL/Redis readiness, Nginx frontend/API routing,
  and dependency checks in an isolated stack; no existing deployment image or
  database volume was replaced.
- The latest image resolved Python 3.14.10, FastAPI 0.162.2,
  SQLAlchemy 2.1.8, OpenCV 5.0.0, MediaPipe 0.10.35, NumPy 2.5.4, and
  scikit-learn 1.9.1. The host regression suite was not run inside this image.
- Two Uvicorn workers initially raced during PostgreSQL `create_all()` and one
  failed on a duplicate table type. PostgreSQL advisory-lock serialization was
  added; both workers then started successfully, survived a backend restart,
  and retained the synthetic database rows across a PostgreSQL restart.
- The retained `pocketcoach-check` services remain healthy, but its backend
  image is from 2026-11-05 and does not represent the current workspace source.
- Nginx served the frontend and `/api/adaptive/capabilities`; PostgreSQL
  persistence across backend and database restarts was verified.
- Synthetic legacy PostgreSQL schema upgrade and idempotent reinitialization
  preserved athlete/session history and verified foreign keys/indexes. A
  forced lock-timeout transaction rolled back, and retry succeeded.
- Checksum-enforced backup/restore retained synthetic user/profile/session
  data; password verification and SQLAlchemy reads passed. A modified dump was
  rejected before a target database was created.
- Live signup/login issued a 900-second access token. Refresh-token rotation
  rejected replay with HTTP 401; logout revoked the replacement refresh token.
  A regression test confirmed unexpired legacy JWTs remain valid until their
  embedded expiry.
- The Redis-backed Nginx rate limit allowed 60 requests and returned HTTP 429
  on request 61; spoofed `X-Forwarded-For` values did not bypass the limit.
- Automated coverage includes authorization/ownership boundaries, input
  validation, password reset, refresh-token rotation/logout, and in-memory/
  Redis rate limiting.
- Final matched clean-image profiles at 2 CPU/1 worker showed 47 baseline
  timeouts at 25 users and none after optimization. At 100 users throughput
  increased from 15.79 to 31.84 req/s and p95 decreased from 23.47 to 16.65
  seconds; at 50 users p95 regressed. The high-concurrency performance gate
  remains failed; see
  [AUTHENTICATED_LOAD_TEST_REPORT.md](./AUTHENTICATED_LOAD_TEST_REPORT.md).
- Isolated live API QA passed signup/login, protected and adaptive profile,
  catalog, skills, session creation/history, pose analysis, refresh rotation
  and alias, replay rejection, logout revocation, and Nginx frontend routing;
  see [QA_REPORT.md](./QA_REPORT.md).

## Not verified

- No independent penetration test, dependency vulnerability scan, public
  infrastructure review, production SMTP delivery, real TLS deployment, real
  Redis outage/reconnect test, or tested monitoring/alert delivery.
- PostgreSQL upgrade and restore used synthetic data, not a sanitized copy of
  production data. The compatibility initialization is not a formal versioned
  migration chain.
- Load testing was local and synthetic, not a sustained soak, production
  capacity test, or realistic camera/video workload.
- The full regression suite ran on the host Python 3.14 environment, not
  inside the new Docker image.
- No accessibility audit or physical iOS/Android camera-device test was
  performed.
- No new model was trained; the current classifier remains experimental and
  unapproved for live coaching.

## Reproducible checks

From the repository root, with dependencies installed:

```powershell
$env:TEST_REDIS_URL = "redis://127.0.0.1:16379/0"
python -m pytest backend\tests -q
python -m compileall -q backend\app backend\tests
python -m pip check
Get-ChildItem frontend -Recurse -Filter *.js |
  ForEach-Object { node --check $_.FullName }
docker compose --env-file .env.example config --quiet
git diff --check
```

The original local validation stack remains available at `127.0.0.1:18001`,
but runs an older backend image. See
[DEPLOYMENT_REPORT.md](./DEPLOYMENT_REPORT.md) for release gates.
