# Monitoring and Alerting Report

Assessment date: 2026-11-08.

## Implemented foundation

- `GET /health` remains a lightweight liveness response.
- `GET /health/ready` probes PostgreSQL and configured Redis; it returns
  structured component statuses and HTTP 503 for required dependency failure.
- The backend container health check now uses readiness rather than only
  process liveness.
- HTTP requests receive an `X-Request-ID`. Completion/failure logs include
  JSON fields for request ID, method, path (without query string), status, and
  duration; authorization headers, request bodies, passwords, and tokens are
  not logged by this middleware.
- Existing Compose health checks cover PostgreSQL, Redis, backend, and Nginx.
  Resource limits are configured for containers.

## Operational monitoring plan

No external metrics or error-tracking dependency was added. This avoids
shipping athlete data to an unconfigured third party. In staging/production,
collect Docker health/restart events and `docker stats`, PostgreSQL connection
and storage metrics, Redis memory/availability, Nginx access/error logs, and
request logs. Export only approved aggregate metrics; define retention and
access controls before collecting identifiers or athlete activity.

Alert on backend unhealthy/restarts, sustained HTTP 5xx, readiness failures,
PostgreSQL connection/storage exhaustion, Redis failures/fallback, Nginx 5xx,
and missing/failed backup artifacts. Route backup failure notifications only
to an HTTPS webhook with a non-sensitive message. Test each alert with a
controlled staging fault and verify delivery/acknowledgment.

## Outstanding

- No metrics backend, dashboard, external error tracker, alert receiver, or
  production notification route is configured.
- No CPU/memory/disk thresholds, retention policy, or alert delivery test has
  been executed.
- Authentication failure events are not yet exposed as an aggregate metric.

Status: **PARTIAL** — dependency readiness and request correlation are
implemented; operational monitoring and alerting remain deployment work.
