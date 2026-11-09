# Authenticated Load Test Report

Assessment date: 2026-11-09. A reusable synthetic workflow runner is provided
at `scripts/authenticated_load_test.py`. It exercises signup, login, protected
profile, adaptive catalog, skills, session creation/history, profile-twin
analytics, pose analysis, refresh, and logout at configurable concurrency.

## Safe execution

Run only against a fresh, isolated Compose project with synthetic credentials,
high test-only rate limits, and a dedicated database. The script creates
accounts and records; do not point it at production or an existing athlete
database. The default profile levels are 10, 25, 50, and 100 concurrent
synthetic users. Capture container CPU/memory and PostgreSQL/Redis metrics
during each profile.

## Results

The test ran through Nginx against an isolated Compose project with a fresh
PostgreSQL volume, Redis, and a test-only limit of 5,000 requests/minute. Ten
readiness requests were used as warm-up. Each virtual user ran a complete
synthetic workflow. Percentiles use nearest-rank and include all measured HTTP
requests in the profile.

| Concurrent users | Requests | Throughput | p50 | p95 | p99 | Errors |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 120 | 14.78 req/s | 413.38 ms | 2,108.08 ms | 2,294.54 ms | 0 / 120 |
| 25 | 300 | 20.50 req/s | 747.09 ms | 4,021.52 ms | 4,677.11 ms | 0 / 300 |
| 50 | 600 | 20.20 req/s | 1,296.50 ms | 8,266.52 ms | 9,689.21 ms | 0 / 600 |
| 100 | 1,200 | 21.14 req/s | 2,525.67 ms | 17,286.82 ms | 18,002.84 ms | 0 / 1,200 |

These are local results with a Compose backend resource cap of 1 CPU/1 GiB.
Latency increases sharply with concurrency and throughput plateaus near
21 requests/second; do not treat zero HTTP failures as acceptable interactive
performance or production capacity. The workflow uses synthetic uniform pose
landmarks and does not model real camera/video frame rates.

## Earlier fresh-image bottleneck isolation

These are preliminary historical trials that preceded the final clean,
matched one-worker comparison below. They use different profile selections
and are retained as diagnostic context, not as the final before/after result.

A fresh backend image was built under isolated tags and tested through Nginx
with synthetic data, a 1 GiB backend memory cap, and a test-only limit of
5,000 requests per minute. The 2-CPU runs used a clean PostgreSQL volume.

| Backend CPU cap | Uvicorn workers | Requests | Elapsed | Throughput | p95 | Errors/timeouts | Peak backend CPU |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 202 | 60.37 s | 3.35 req/s | 30.02 s | 49.01% | about 105% |
| 2 | 1 | 133 | 62.26 s | 2.14 req/s | 30.05 s | 75.19% | 216.12% |
| 2 | 2 | 150 | 68.82 s | 2.18 req/s | 30.07 s | 66.67% | 226.53% |

These are short local stress profiles, not capacity guarantees. The earlier
cached-image 10/25/50/100-user results above are historical and are not directly
comparable to the fresh dependency resolution. On the fresh image, increasing
the CPU cap and then adding a second worker did not improve the 100-user result:
requests continued to time out at the client’s 30-second limit.

The hottest work was on the backend, especially signup/login. The current async
auth handlers perform PBKDF2 hashing and verification synchronously. A separate
one-CPU microbenchmark took 12.71 seconds for 100 hashes and 13.47 seconds for
100 verifications; 20 concurrent threads took 89.34 seconds for 100 hashes on
one CPU. The password work factor was not reduced. During the two-worker run,
PostgreSQL’s busiest measured statement (athlete insert) averaged 2.922 ms
(34.477 ms maximum); other top statements averaged below 8 ms. Redis `EVAL`
averaged 0.412 ms server time and `INCR` 0.016 ms. PostgreSQL had at most 20
client connections and one sampled active query. Backend logs did record Redis
connection timeouts/fallbacks while the application was saturated; Redis
command execution itself was not the dominant measured cost.

Enabling two Uvicorn workers initially reproduced a PostgreSQL startup race:
both workers attempted `create_all()` concurrently and one failed with a
duplicate `pg_type` error. PostgreSQL advisory-lock serialization was added to
database initialization; the fresh image then started both workers and
survived a backend restart. The two-worker load profile still failed the
latency/error gate, so no worker-count change was made to the original
deployment configuration.

## Latest matched clean-image comparison

The final before/after comparison used separate, brand-new isolated Compose
projects and PostgreSQL volumes, sequentially through Nginx. The baseline was
`pocketcoach-backend:verification-20261108-init-lock`; the optimized build was
`pocketcoach-backend:optimization-gstack-final-20261109`. Both used the same
2-CPU/1-worker backend limit, 1 GiB memory limit, fresh PostgreSQL 16 and Redis
8, 5,000-requests/minute test-only limit, 30-second client timeout, runner
revision, ten readiness warm-ups, and 10/25/50/100 user profiles. The final
runner's responsiveness probe called the FastAPI
`/api/adaptive/capabilities` route through Nginx every 100 ms with a 2-second
timeout. Each virtual user attempted a 12-request workflow.

| Users | Requests, baseline → optimized | Throughput, baseline → optimized | p50, baseline → optimized | p95, baseline → optimized | p99, baseline → optimized | Main-workflow timeouts, baseline → optimized | Backend-probe p95/errors, baseline → optimized |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 120 → 120 | 9.30 → 25.05 req/s | 513 → 72 ms | 3,994 → 1,818 ms | 4,827 → 2,118 ms | 0 → 0 | 2,016 ms / 2 → 178 ms / 0 |
| 25 | 160 → 300 | 1.52 → 22.92 req/s | 3,553 → 152 ms | 30,015 → 5,610 ms | 30,028 → 8,232 ms | 47 → 0 | 2,020 ms / 47 → 196 ms / 0 |
| 50 | 600 → 600 | 21.51 → 25.52 req/s | 1,276 → 138 ms | 7,978 → 9,087 ms | 8,937 → 12,511 ms | 0 → 0 | 2,023 ms / 8 → 163 ms / 0 |
| 100 | 1,200 → 1,200 | 15.79 → 31.84 req/s | 3,652 → 186 ms | 23,470 → 16,646 ms | 26,931 → 20,791 ms | 0 → 0 | 2,026 ms / 33 → 196 ms / 0 |

No HTTP error responses occurred in the authenticated workflows. At 25 users,
47 baseline requests timed out and only 160 requests were attempted because
users stop their workflow after signup/login failure. At 100 users, throughput
approximately doubled and p95 improved by 29%, but 16.65 seconds p95 remains
too high for an interactive experience. At 50 users, throughput improved but
p95/p99 regressed; the result is not a uniform latency improvement.

The backend responsiveness probe is a lightweight endpoint check, not direct
asyncio scheduler-lag instrumentation. It timed out frequently on the baseline
and had no errors on the optimized build. Container peaks observed during
sampling were:

| Container | Baseline peak CPU / memory | Optimized peak CPU / memory |
|---|---:|---:|
| Backend (2-CPU / 1-GiB limit) | 155.34% / 117.0 MiB | 213.38% / 113.3 MiB |
| PostgreSQL (1-CPU / 1-GiB limit) | 53.14% / 71.4 MiB | 65.20% / 61.8 MiB |
| Redis (0.5-CPU / 256-MiB limit) | 27.20% / 8.8 MiB | 16.35% / 6.3 MiB |
| Nginx (0.5-CPU / 256-MiB limit) | 30.80% / 5.0 MiB | 25.46% / 5.0 MiB |

Sampled PostgreSQL client connections peaked at 15 baseline versus 11
optimized; sampled active queries peaked at 1 versus 2. These samples do not
show database connection exhaustion or a long-running SQL query as the cause
of the observed baseline stalls. Resource peaks are observed samples, not
capacity guarantees.

## Historical single-core release-gate sample

The following resource table comes from an earlier single-core run and is
superseded for comparison purposes by the matched clean-image results above.

The Docker CPU/memory sampler was started alongside the run; its final
aggregation is recorded from a separate 100-user repeat on the same isolated
test database after earlier profiles had left synthetic accounts. Docker
sampled peak CPU/memory (approximately, once per second):

| Container | Peak CPU | Peak memory |
|---|---:|---:|
| Backend (limit 1 CPU / 1 GiB) | 106.96% | 116.2 MiB |
| PostgreSQL (limit 1 CPU / 1 GiB) | 36.00% | 65.4 MiB |
| Redis (limit 0.5 CPU / 256 MiB) | 32.09% | 7.7 MiB |
| Nginx (limit 0.5 CPU / 256 MiB) | 20.72% | 7.7 MiB |

That repeat returned 1,200/1,200 HTTP 200/201 responses at 15.96 req/s,
p50 2,929.63 ms, p95 23,350.41 ms, p99 26,131.85 ms, maximum 27,198.27 ms.
This second run is resource-sampled but is not directly comparable because
the database already contained earlier synthetic test accounts. Per-stage DB
connection peaks were not recorded. Add a sustained soak test and realistic
pose/video workloads before setting capacity targets. No production capacity
is claimed.

Status: **PARTIAL / performance gate FAIL** — the final clean 100-user
comparison improved throughput and p95, but optimized p95 remains 16.65
seconds; the 50-user p95 also regressed. The 25-user baseline had 47 client
timeouts. Do not treat this local short run as production capacity. Sustained
load, real device/video, and production capacity remain unverified.
