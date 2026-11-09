# Code Review Report

Assessment date: 2026-11-09. This was an internal review of the performance
and authentication changes, not a GStack `/review` command or a whole-repository
independent audit.

## Scope

- Password-hash execution and reset-token consumption in
  `backend/app/services/auth_service.py`.
- Signup, login, reset, and refresh flows in `backend/app/routes/auth.py`.
- Readiness handling in `backend/app/main.py`.
- Sync SQLAlchemy/pose route dispatch changes in the affected
  `backend/app/routes/` modules.
- Focused auth/hash regression tests, authenticated load-test harness, and
  isolated performance Compose overlay.

## Findings

| # | Severity | Finding | Disposition |
|---|---|---|---|
| 1 | MEDIUM | The compatibility `/api/auth/refresh` route no longer renews using only an access JWT. Retaining that contract would bypass refresh-token rotation and could extend a stolen access token indefinitely. | Intentional security change. Both refresh routes now require and rotate a refresh token; the current frontend uses `/api/auth/token/refresh`. Existing external clients using access-token-only renewal must migrate. |

No other confirmed actionable correctness, resource-lifecycle, or security
defect was identified in the reviewed change scope. This is not a claim that
the entire application is defect-free.

## Review checks

- PBKDF2 work factor and existing PBKDF2/bcrypt verification formats are
  preserved. Password hashing uses a bounded, single-worker executor; queue
  saturation returns an explicit HTTP 503 with `Retry-After`.
- Signup/login release database transactions before awaiting hash work. Login
  rechecks the verified password hash under a row lock before issuing a
  refresh token, preventing a concurrent reset from restoring a session.
- Password-reset tokens are consumed atomically and once; sensitive reset
  links and recipients are not logged.
- Blocking sync SQLAlchemy and pose work is dispatched through FastAPI's
  synchronous route execution rather than occupying the async event loop.
- Refresh rotation, replay rejection, logout revocation, short-lived access
  tokens, and legacy signed JWT acceptance are covered by regression tests.
- PostgreSQL connection and transaction behavior, startup initialization,
  request failure handling, and bounded hashing have focused tests.

The full backend suite passed with Redis 8 integration enabled: 118 passed,
zero skipped. Matched performance testing and its remaining high-concurrency
latency failure are documented in
[AUTHENTICATED_LOAD_TEST_REPORT.md](./AUTHENTICATED_LOAD_TEST_REPORT.md).

## Limitations

No independent external code audit, whole-repository review, browser-driven
code review, or deployment-level resource soak was performed. The accepted
LOW risk of copied access JWTs remaining valid until expiry is documented in
[SECURITY_AUDIT.md](./SECURITY_AUDIT.md).
