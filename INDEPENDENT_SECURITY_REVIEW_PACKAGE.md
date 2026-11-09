# Independent Security Review Package

Prepared 2026-11-08 for a future independent reviewer. No independent
penetration test is claimed.

## System overview

Vanilla JavaScript frontend and camera/MediaPipe processing; FastAPI API;
SQLAlchemy models; PostgreSQL persistence; Redis-backed rate limiting with a
documented in-memory fallback; Nginx reverse proxy; Docker Compose deployment.
The backend is not published directly to the host in the provided Compose
configuration.

## Authentication and controls

- HS256 access JWTs are newly issued for 15 minutes; existing signed tokens
  retain their embedded expiry during rollout.
- Opaque refresh tokens are stored as keyed hashes, rotated conditionally, and
  rejected on replay. Logout revokes the submitted refresh token.
- Password reset uses single-use hashed tokens, and SMTP fallback does not log
  reset links or recipient addresses.
- Protected routes verify active accounts. Authorization tests cover roles and
  cross-user ownership for sessions/profiles.
- Production startup rejects weak/default signing secrets and wildcard CORS;
  production SMTP requires STARTTLS and coherent credentials.
- Redis rate limiting was verified through Nginx. Rate-limit fallback is
  process-local when Redis is unavailable.

## Known residuals and evidence

- An already-issued access token remains usable until expiry after logout
  (maximum 15 minutes for new tokens). No global denylist was added.
- A shared signing-secret exposure requires an incident decision and possible
  key rotation; rotation invalidates outstanding JWTs.
- Internal tests/live checks cover malformed tokens, refresh replay/logout,
  ownership boundaries, adaptive validation, and rate limiting. See
  `SECURITY_AUDIT.md` and `TESTING_REPORT.md`.
- No third-party penetration test, dependency vulnerability scan, external
  infrastructure review, production TLS check, or SMTP delivery test was
  completed.

## Requested independent review scope

1. Validate deployed secrets, TLS, CORS/preflight, trusted proxy boundaries,
   container privileges, and database/Redis network permissions.
2. Test authentication/session lifecycle, reset abuse, refresh-token theft/
   replay, account enumeration, and access-token logout residual.
3. Test cross-user/coach authorization and adaptive profile/session isolation.
4. Review SQLAlchemy queries, request validation, uploads, error disclosure,
   browser XSS/CSRF/storage protections, and dependency/container advisories.
5. Test rate limiting with multiple workers and Redis outage/recovery.
6. Deliver a scoped report with evidence, severity, remediation, and retest.

Testing must use a written authorization scope and non-production synthetic
accounts/data. Do not test against public users without explicit authorization.
