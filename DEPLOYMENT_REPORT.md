# Deployment Validation Report

Assessment date: 2026-11-09. Local validation only; this is not production
certification or approval for external access.

## Result summary

| Component/check | Result | Evidence |
|---|---|---|
| Docker Compose | PASS | Base and TLS override configurations validated. |
| Fresh-image Compose deployment | PASS, isolated | Built separate `pocketcoach-backend:verification-20261108` and `pocketcoach-backend:verification-20261108-init-lock` tags without replacing the retained deployment. The latest image started against fresh PostgreSQL/Redis services; readiness, Nginx frontend, and adaptive API returned HTTP 200. The two-worker image started after PostgreSQL initialization was serialized. |
| Retained `pocketcoach-check` stack | PARTIAL | Its services remain healthy on port 18001 with the original database volume preserved, but its backend image dates from 2026-11-05 and does not contain the latest readiness route. A request to `/health/ready` receives the Nginx frontend fallback HTML with HTTP 200, not a readiness payload. It was left untouched. |
| PostgreSQL persistence | PASS, synthetic | On the fresh isolated image, counts of 84 athletes, 1 session, and 26 refresh tokens were unchanged across a PostgreSQL restart and a two-worker backend restart; readiness remained HTTP 200. The original named volume was not used. |
| PostgreSQL compatibility upgrade | PARTIAL | Synthetic legacy schema upgrade preserved linked athlete/session history; foreign keys and indexes verified. A forced lock-timeout transaction rolled back cleanly and retry succeeded. No production-like copy or versioned migration chain was tested. |
| PostgreSQL backup/restore | PARTIAL | Checksummed custom-format dump restored synthetic account/profile/session data into a separate database; password verification and SQLAlchemy reads passed. Tampering was rejected before target creation. Scheduled backup, alert delivery, off-host storage, and production-sized recovery remain unverified. |
| Redis and Nginx | PASS, local | Redis health/ping and Nginx frontend/API routing were exercised. Live Redis-backed rate limiting returned 60 HTTP 200 and one HTTP 429; spoofed `X-Forwarded-For` did not evade the limit. |
| Authentication | PASS, focused | New access JWT lifetime is 900 seconds; refresh replay and post-logout refresh returned HTTP 401. Existing unexpired legacy access tokens remain valid until their embedded expiry. |
| Backend regression | PASS, local | 118 tests passed, zero skipped, with a separate Redis 8 integration instance; see [TESTING_REPORT.md](./TESTING_REPORT.md). |
| Authenticated workflow load | FAIL, not production-ready | Final matched fresh-image 2-CPU/1-worker runs improved 100-user throughput from 15.79 to 31.84 req/s and p95 from 23.47 to 16.65 s; the optimized p95 remains too high, the 50-user p95 regressed, and the baseline had 47 timeouts at 25 users. See [AUTHENTICATED_LOAD_TEST_REPORT.md](./AUTHENTICATED_LOAD_TEST_REPORT.md). |
| Optimized API QA | PASS, isolated | Synthetic live checks passed signup/login, profile, adaptive training/catalog, skills, session create/history, analysis, refresh rotation/replay, logout revocation, and Nginx frontend routing; responsive browser/device QA remains unverified. |

These are local synthetic results. They do not establish production capacity,
recoverability from a site-wide event, or behavior on production hardware.

## Infrastructure and security limitations

TLS and base Compose syntax passed validation, but no real certificate or
public HTTPS endpoint was deployed. SMTP configuration checks passed, but no
provider delivery was tested. Readiness checks and structured request logging
exist; no dashboards, alert delivery, or on-call workflow was exercised.

No independent penetration test, dependency vulnerability scan, external
infrastructure review, real Redis outage/reconnect exercise, production-sized
restore drill, or physical Android/iOS camera test was performed. The fresh
image’s dependency consistency and local health checks passed, but the
high-concurrency latency gate failed. Security coverage and residual token risk are recorded in
[SECURITY_AUDIT.md](./SECURITY_AUDIT.md).

## Remaining release gates

1. Rehearse PostgreSQL upgrade and recovery using sanitized, representative
   production-sized data; establish and verify a formal migration chain.
2. Configure encrypted, access-controlled off-host backups; exercise scheduled
   execution and alert delivery; measure restore time against approved RPO/RTO.
3. Configure and verify real SMTP, TLS/certificate renewal, explicit CORS
   origins, and managed secrets.
4. Deploy monitoring dashboards, actionable alerts, retention, and incident
   procedures; test their delivery.
5. Complete an independent authenticated security assessment and dependency
   review, then remediate findings.
6. Resolve high-concurrency CPU/event-loop saturation without reducing the
   password-hashing work factor, then run sustained tests with realistic
   pose/video payloads and production-like resources. Keep one worker until
   deployment-level performance is revalidated.
7. Complete physical-device camera, permission, and recovery testing before a
   consented athlete pilot.

**Decision: PARTIAL — not production-ready and not approved for public launch.**
The original `pocketcoach-check` stack and its named PostgreSQL volume are
preserved on localhost port 18001; that running stack is an older image, not
the current workspace source. The four newly created clean/final comparison
projects and their synthetic PostgreSQL volumes were removed after
measurement, along with the dedicated regression Redis container. Earlier
pre-existing synthetic benchmark projects and volumes were left untouched.
Both verification image tags and the separate
`pocketcoach-validation_postgres_data` volume were preserved. No commit or
push was made.
