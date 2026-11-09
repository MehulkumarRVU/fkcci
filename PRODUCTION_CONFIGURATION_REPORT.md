# Production Configuration Report

Assessment date: 2026-11-08. No public deployment or valid TLS endpoint was
tested.

## Configuration changes

- Startup rejects short/default production signing secrets and wildcard CORS.
- Production requires SMTP host/from-address, STARTTLS, and either both SMTP
  username/password or neither. SMTP port and timeout are bounded, and the
  send operation has a finite timeout.
- Compose keeps PostgreSQL and backend ports private; Nginx is the public
  ingress. The separate `docker-compose.tls.yml` and `nginx.tls.conf` provide
  an HTTPS termination option with HTTP redirect, TLS 1.2/1.3, and HSTS.
- The signing secret remains stable; no active sessions were invalidated.
- Production secrets are required at Compose interpolation and must be
  supplied by the deployment secret manager or protected environment file.
- CORS remains environment-configured; set exact HTTPS frontend origins and
  test preflight from the deployed origin.

## Not verified

- No real SMTP provider/credentials or password-reset delivery was available.
- No certificate/private key was supplied; the TLS Compose configuration was
  syntax-checked only. HTTP redirect, certificate chain, renewal, HSTS, and
  browser camera access over HTTPS remain unverified.
- No production CORS origin or credentialed preflight was exercised.
- No secret-manager integration or rotation procedure was run. Preserve the
  JWT signing key during gradual token-lifetime migration; rotate it only for a
  documented compromise/rotation event with a user-session plan.

## Deployment requirements

Keep `.env` and certificate private keys out of source control; restrict
filesystem and backup permissions; use unique database/Redis credentials;
restrict ingress to HTTPS; configure `CORS_ALLOWED_ORIGINS` explicitly; verify
SMTP STARTTLS and sender alignment; and rehearse secret rotation in staging.
Use DNS/ACME or the infrastructure provider's certificate lifecycle manager.
Do not advertise HTTPS as active until a valid externally reachable endpoint
and renewal are tested.

Status: **PARTIAL** — guardrails and TLS configuration exist, but real
production services and certificates are not configured or verified.
