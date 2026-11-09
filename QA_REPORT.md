# QA Report

Assessment date: 2026-11-09. Checks used an isolated synthetic deployment; no
retained athlete database or production deployment was modified.

## Automated and API workflow results

The optimized backend image ran behind Nginx with fresh PostgreSQL and Redis
containers. Direct API smoke checks used a unique synthetic athlete account.

| Workflow/check | Result |
|---|---|
| Nginx frontend root | PASS — HTTP 200, HTML response |
| Signup and login | PASS — HTTP 201 and HTTP 200 |
| Protected profile, adaptive profile/catalog, skills | PASS — HTTP 200 |
| Session creation and history | PASS — HTTP 201 and HTTP 200 |
| Pose/session analysis | PASS — HTTP 200 |
| Refresh-token rotation | PASS — HTTP 200 |
| Replay of replaced refresh token | PASS — rejected with HTTP 401 |
| Legacy refresh alias with a refresh token | PASS — rotates successfully |
| Logout and subsequent refresh | PASS — logout HTTP 200; revoked token rejected with HTTP 401 |
| Full backend suite with Redis 8 | PASS — 118 passed, zero skipped |

The full synthetic workflow load test also exercised signup, login, protected
profile, adaptive catalog, skills, session creation/history, profile-twin
analytics, pose analysis, refresh, and logout at 10, 25, 50, and 100 users.
The performance report contains the measured responses and latency results.

## Not verified

- No browser-driven visual/responsive test, accessibility audit, or physical
  iOS/Android camera-device workflow was completed.
- No SMTP delivery, real TLS certificate, production monitoring/alert
  delivery, independent penetration test, or public deployment was exercised.
- Synthetic uniform landmarks do not represent real camera video, varied
  athletes, or production usage.

See [TESTING_REPORT.md](./TESTING_REPORT.md) and
[DEPLOYMENT_REPORT.md](./DEPLOYMENT_REPORT.md) for broader validation and
remaining release gates.
