# Performance Profiling Report

Assessment date: 2026-11-09. All profiling ran in isolated synthetic Compose
projects; no retained service or volume was used.

## Instrumentation and coverage

The isolated ASGI wrapper in `scripts/phase2_profile_runtime.py` adds a
10-ms event-loop-lag sampler and captures:

- SQLAlchemy pool checkout wait (`QueuePool._do_get`) and DBAPI statement
  execution wall time by SQL verb.
- Redis/in-memory rate-limiter call wall time.
- Synchronous password hash/verify computation time and, on the optimized
  image, async end-to-end time and executor queue wait.
- Password-executor worker count, pending queue high-water mark, AnyIO thread
  limiter state, process thread count, and GC collection counts.

The helper uses private SQLAlchemy pool and `ThreadPoolExecutor` implementation
details and is diagnostic-only. It is mounted only by
`docker-compose.phase2-profiling.yml`; it is not part of the production image
or normal application entrypoint.

## Authentication and executor measurements

The optimized fresh 50-user diagnostic run attempted 600 workflow requests
with zero workflow errors/timeouts. Endpoint distributions:

| Endpoint | Requests | p50 | p95 | Maximum |
|---|---:|---:|---:|---:|
| Signup | 50 | 3,652 ms | 6,778 ms | 7,041 ms |
| Login | 50 | 8,051 ms | 9,993 ms | 10,088 ms |
| Protected `/me` | 50 | 190 ms | 408 ms | 432 ms |
| Pose analysis | 50 | 222 ms | 358 ms | 576 ms |
| Adaptive profile | 50 | 183 ms | 418 ms | 478 ms |
| Adaptive catalog | 50 | 133 ms | 212 ms | 284 ms |
| Profile-twin analytics | 50 | 162 ms | 306 ms | 402 ms |

Password operations in that run:

| Operation | Samples | p50 | p95 | p99 / maximum |
|---|---:|---:|---:|---:|
| PBKDF2 hash computation | 50 | 132 ms | 201 ms | 218 ms |
| Password verification computation | 50 | 188 ms | 281 ms | 367 ms |
| Hash async end-to-end | 50 | 3,125 ms | 5,991 ms | 6,222 ms |
| Verify async end-to-end | 50 | 7,942 ms | 9,871 ms | 9,930 ms |
| Executor queue wait | 100 | 6,088 ms | 9,606 ms | 9,721 / 9,745 ms |

The executor had one worker and a queue high-water mark of 49; the queue was
empty after the profile. The end-to-end password timers include waiting and
scheduling; they are not pure CPU time. The large gap between hash computation
and queue wait establishes that queued serialization, rather than a single
hash's runtime alone, dominates the auth tail at this load. PBKDF2 remains at
100,000 iterations; no password or token security setting was changed.

## Event loop, database, Redis, and resource observations

| Signal at 50 users | Baseline | Optimized | Interpretation |
|---|---:|---:|---|
| Event-loop lag p95 / p99 | 334 / 473 ms | 20 / 35 ms | Large, repeatable reduction after async-boundary changes |
| SQLAlchemy pool checkout p95 | 0.088 ms | 0.092 ms | No evidence of material pool-acquisition delay |
| SQL `SELECT` execution p95 / max | 6.46 / 21.73 ms | 25.91 / 87.52 ms | Optimized queries are slower under this CPU-saturated run but remain far below auth endpoint tails |
| SQL `INSERT` execution p95 | 3.32 ms | 17.09 ms | Not a multi-second cause |
| SQL `UPDATE` execution p95 | 1.73 ms | 16.32 ms | Not a multi-second cause |
| Redis limiter wall p95 | 189.18 ms | 22.73 ms | Includes event-loop/client/network delay, not Redis-only time |
| Redis `EVAL` server mean | 74.95 µs | 54.83 µs | Server-side command execution is small |
| Redis `INCR` server mean | 22.61 µs | 7.70 µs | Server-side command execution is small |
| Backend sampled CPU maximum | 122.45% | 208.47% | Optimized image can use nearly both CPUs |
| Backend sampled memory maximum | 111.1 MiB | 106.1 MiB | Not near the 1-GiB limit |
| PostgreSQL sampled CPU / memory | 25.13% / 58.4 MiB | 39.20% / 59.0 MiB | Moderate sampled usage |
| Redis sampled CPU / memory | 8.84% / 5.7 MiB | 2.37% / 5.7 MiB | Not a resource bottleneck in the observed sample |
| Nginx sampled CPU / memory | 6.65% / 3.6 MiB | 21.83% / 3.5 MiB | Nginx was not isolated from app/middleware cost |

Docker resource values are maxima from a short approximately 1-second sampling
window (14 samples per container), not guaranteed whole-run peaks. PostgreSQL
activity was queried after the benchmark, not sampled continuously; that
post-run snapshot is not evidence of peak query concurrency. `pg_stat_statements`
was not available in the test database, so query aggregation relies on
SQLAlchemy cursor-event measurements instead. Pool checkout timing was
directly recorded. Only the Redis-backed limiter bucket was observed; no
in-memory fallback sample occurred during the measured profile.

GC counters for the 50-user run were 26 generation-0 collections, 2
generation-1, and 1 generation-2 on the optimized image; the baseline recorded
22, 2, and 1. These counters do not measure stop-the-world pause duration.
AnyIO's default limiter has 40 tokens and had no borrowed tokens/tasks waiting
at the final snapshot. This is a snapshot, not a peak concurrent-thread
measurement.

## CPU profiling and non-auth work

Pylance Tachyon CPU sampling was attempted but requires Python 3.15.0b3 or
newer; the selected host interpreter is Python 3.14.2. No `cProfile`,
`py-spy`, Memray, or instruction-level CPU profile was completed. The
password function wall timers, event-loop lag, and container CPU are direct
measurements, but they do not provide a complete per-function CPU flame graph.
The synthetic users were created with the current PBKDF2 format, so bcrypt
verification was not exercised; its runtime under concurrent load remains
unknown.

The pose-analysis p95 was 358 ms for the one-frame test payload. This is not a
representative multi-frame camera/video workload and does not establish a
production pose-analysis bound. Nginx and application middleware were
included in end-to-end measurements; their individual fractions were not
separated.

## Reproduction

The isolated helper can be exercised with a separate Compose project and
synthetic environment:

```powershell
$env:BACKEND_IMAGE = "pocketcoach-backend:optimization-gstack-final-20261109"
$env:PROFILE_BACKEND_CPUS = "2.0"
$env:PROFILE_UVICORN_WORKERS = "1"
$env:NGINX_PORT_MAPPING = "18083:80"
docker compose --env-file .env.example `
  -f docker-compose.yml `
  -f docker-compose.performance.yml `
  -f docker-compose.phase2-profiling.yml `
  -p pocketcoach-phase2-optimized up -d
python scripts\authenticated_load_test.py `
  --base-url http://127.0.0.1:18083 `
  --concurrency 50 `
  --cooldown-seconds 0 `
  --probe-interval-seconds 0.1
```

Set isolated test database credentials and required secrets in the invoking
shell; do not use production values. Use a unique project name and a disposable
database volume, and remove only that test project after collection.
