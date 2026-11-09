# Security Assessment

Status: focused internal code review, automated regression coverage, and live
authentication/rate-limit checks completed on 2026-11-08. This is not an
independent security assessment, penetration test, or third-party certification.

## Findings and disposition

| # | Severity | Finding | Status |
|---|---|---|---|
| 1 | MEDIUM | Password-reset email fallback previously logged reset URLs/tokens and recipient addresses. | Fixed |
| 2 | LOW | Browser logout previously removed local credentials without revoking the server-side refresh token. | Fixed |
| 3 | LOW | A copied access JWT remains usable until its expiry after logout. | Accepted residual risk; maximum 15 minutes for newly issued tokens |

The email fallback now logs only that delivery is disabled, and production
configuration requires SMTP host/from-address settings. Previously written
logs may still contain sensitive reset links; apply the deployment's
log-retention and incident-response policy to historical logs.

Logout revokes the submitted refresh token. Refresh tokens are opaque, stored
as keyed hashes, rotated on renewal, and cannot be reused after rotation. The
live flow verified the new access-token lifetime is 900 seconds, old-token
replay returns HTTP 401, and refresh after logout returns HTTP 401.

## Token lifetime migration

Keep the existing signing key stable during this transition. Existing signed
access JWTs continue to be accepted until their own embedded `exp` claim;
legacy seven-day tokens are not revoked just because the new lifetime is
shorter. New access JWTs issued at login or refresh are limited to 15 minutes.
The existing refresh-token flow continues to renew access, rotating the
refresh token on every successful renewal and rejecting replay. Logout keeps
revoking the submitted refresh token server-side.

No mass session invalidation or access-token denylist was introduced. Rotating
the signing key would invalidate existing JWTs and should be reserved for an
actual signing-key exposure or token-compromise response. Immediate access
token revocation remains a future option if the threat model or policy changes.

Immediate access-token invalidation was not added: it would require a
denylist/session lookup on protected requests. The bounded 15-minute access
token lifetime was judged proportionate for the current threat model. Revisit
this if policy requires immediate logout or high-risk account actions.

## Assessment coverage

- **Authorization and session isolation:** automated regression tests cover
  protected routes, coach/athlete roles, and cross-user ownership boundaries;
  no independent adversarial session-isolation assessment was performed.
- **Token handling:** automated tests and live Compose signup/login/refresh/
  logout checks cover short-lived access JWTs, refresh rotation/replay, and
  logout revocation. Inactive accounts are denied protected access and refresh.
- **Rate limiting:** the live Nginx path enforced a Redis-backed limit of 60
  allowed requests per window; request 61 returned HTTP 429. Attempts to vary
  `X-Forwarded-For` did not evade the limit because Nginx replaces that header.
- **Input validation:** automated tests cover malformed/oversized refresh
  tokens and adaptive request validation. Invalid signup email was rejected
  during the live smoke test. The complete backend suite passed 111 tests with
  the Redis integration test enabled.
- **Request/database construction and upload surface:** the prior focused code
  review found no other actionable issue in its reviewed scope.

Rate limiting falls back to in-memory buckets if Redis is unavailable. In
that mode, limits are process-local and are not shared across instances; this
is a documented availability fallback, not equivalent to centralized limits.

## Production requirements and remaining limits

Use a unique high-entropy `SECRET_KEY`, explicit HTTPS CORS origins, working
SMTP, HTTPS frontend/API transport, protected database/Redis access, backups
with a restore test, monitoring, and restricted log retention. Do not treat
`.env.example` values as deployable credentials.

No third-party penetration test, dependency vulnerability scan, production
infrastructure review, comprehensive authenticated manual assessment, or real
Redis outage/reconnect test was performed. These results are targeted internal
checks, not evidence that the application is secure for public deployment.
