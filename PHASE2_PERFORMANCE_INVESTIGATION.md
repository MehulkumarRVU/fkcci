# Phase 2 Performance Investigation

Assessment date: 2026-11-09. Investigation only; no application, authentication,
database, or deployment behavior was changed. The retained deployment and its
database volume were not used.

## Executive result

**Status: PARTIAL — the production performance gate still fails.**

The optimized image substantially reduced event-loop scheduling lag, but the
single-worker password executor now forms a measurable queue under concurrent
signup/login traffic. At 50 users, password computation itself takes roughly
0.20–0.28 seconds at p95, while executor queue wait reaches 9.61 seconds at
p95. The resulting 50-user login p95 is about 10 seconds. This is the strongest
remaining confirmed bottleneck. The 100-user profile also retains 14.62 seconds
p95.

Database pool checkout wait is negligible in the measured runs. PostgreSQL
statement execution and Redis server command time do not explain the dominant
authentication tail. No memory pressure was observed; GC pause duration was
not measured, so smaller GC effects cannot be excluded. Pose analysis is not
representative enough to clear as a production concern: the benchmark uses one
uniform synthetic frame.

The Phase 1 50-user p95 regression (7.98 s baseline versus 9.09 s optimized)
did not recur in four fresh paired Phase 2 runs. The Phase 2 optimized p95
median was lower, but its p99 median was slightly higher. Four repeats are
descriptive, not sufficient for a formal significance claim.

## Repository, image, and workflow identity

- Git `HEAD`: `7c13fe8c158346229cd58d07977f450cffe2b4c4`.
- The worktree was already dirty with 121 changed/untracked paths, including
  tracked `.venv` files and application, frontend, configuration, and report
  changes. All were preserved. The image builds do not correspond to a clean
  `HEAD`; selected source hashes are recorded below.
- Baseline: `pocketcoach-backend:verification-20261108-init-lock`,
  image ID `sha256:9eba128bc39bfe5fec6b316b54e3cb8067cccd0a9b9a930bdba85740f8567a93`.
- Optimized: `pocketcoach-backend:optimization-gstack-final-20261109`,
  image ID `sha256:4a28fb933553c11e9484e051077d6d5531d3d39d247ba29a32c8717b211454b5`.
- The optimized image's selected auth service, auth route, database, rate
  limiter, and analysis source hashes match the corresponding workspace files.
  Baseline auth service, auth route, and analysis differ; its database and
  rate-limit files match the workspace.
- Selected SHA-256 identities:

  | File | Baseline image | Optimized image / workspace |
  |---|---|---|
  | `app/services/auth_service.py` | `6d336890c4ff55e70cfaefb78d493b9e56c0d4e27b26a875f2a9ef4f065e3b70` | `90e7fb00221be61d9b8c37900e7fd345ce2b2ca7dc297907ac071761f9cf3a41` |
  | `app/routes/auth.py` | `5e842a920b89ff8cd230189f07f43923126c523226b24360cde1a63ab7db2ea0` | `214112846f9654a57dc2c521d78f4b6711a6dfa0831d960e32293e59f960b34a` |
  | `app/database.py` | `bce1381db04100b416d43ddabd298726819aecf464f9bb371b341a17b6c5a166` | same |
  | `app/middleware/rate_limit.py` | `cda05feaa7587bd1dc69bb063609dac1a68be5167f85c36865c3f3abb34b59f1` | same |
  | `app/routes/analysis.py` | `e6601871973803b42ef14804a21587b4526b859d111f6d4b2a3e225cd742968d` | `e5890b80fa849f4f8f6c7657ae81d4ac816c892437fefface3aa79f477317abb` |
- GStack and Bun are unavailable; Claude Code did not expose GStack slash
  commands. No GStack command was run. The equivalent investigation was
  performed manually. Pylance CPU sampling was also unavailable because the
  selected Python 3.14.2 interpreter is below that profiler's 3.15.0b3
  requirement.

The host was Windows with Docker Desktop server 29.5.3 (8 host CPUs and about
8.2 GiB RAM); the host load runner used Python 3.14.2, and the backend images
used Python 3.14.10. The dirty worktree means neither image is identified by
`HEAD` alone; the tags, immutable image IDs, and selected source hashes above
are the reproducible identities.

## Test method

Both image tags ran through Nginx in separately named isolated Compose
projects, each with a fresh PostgreSQL volume and Redis 8. The backend limit
was 2 CPUs and 1 GiB, with one Uvicorn worker; PostgreSQL was limited to 1 CPU
and 1 GiB, Redis to 0.5 CPU and 256 MiB, and Nginx to 0.5 CPU and 256 MiB.
The test-only rate limit was 5,000 requests/minute. Ten readiness requests
warmed each run. The unchanged authenticated synthetic runner executed signup,
login, protected profile, adaptive/catalog, skills, session, profile-twin,
single-frame pose analysis, refresh, and logout workflows. Each 50-user run
attempted 600 requests. A 100 ms lightweight API responsiveness probe had a
2-second timeout. Phase 2 projects and their synthetic volumes were removed
after profiling; both tagged images were retained.

An isolated Compose override mounted `scripts/phase2_profile_runtime.py`,
which directly sampled event-loop scheduling lag at 10 ms intervals and
instrumented SQLAlchemy pool checkout and statement timings, Redis-backed rate
limiter wall time, password-operation timing, GC collection counts, and
thread-pool state. A separate 50-user pair used approximately 1-second Docker
resource samples. Profiler timings include instrumentation overhead and are
diagnostic, not production capacity measurements.

## Corrected one-run profiles at each concurrency

Each image started with a fresh database. Concurrency levels were run
sequentially within that image's project. These are one instrumented run per
level; the separate four-pair 50-user repeat is the more useful comparison.

| Users | Image | Throughput | p50 | p95 | p99 | Workflow errors/timeouts | Event-loop lag p95 / p99 | Probe p95 / errors |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 10 | Baseline | 19.12 req/s | 262 ms | 1,920 ms | 2,525 ms | 0 / 0 | 197 / 351 ms | 1,488 ms / 0 |
| 10 | Optimized | 32.34 req/s | 80 ms | 1,498 ms | 1,733 ms | 0 / 0 | 9 / 20 ms | 75 ms / 0 |
| 25 | Baseline | 20.82 req/s | 549 ms | 4,457 ms | 4,703 ms | 0 / 0 | 372 / 455 ms | 2,022 ms / 4 |
| 25 | Optimized | 35.06 req/s | 95 ms | 3,580 ms | 4,047 ms | 0 / 0 | 15 / 41 ms | 111 ms / 0 |
| 50 | Baseline | 21.50 req/s | 1,198 ms | 8,497 ms | 8,793 ms | 0 / 0 | 336 / 473 ms | 2,020 ms / 8 |
| 50 | Optimized | 34.78 req/s | 175 ms | 7,066 ms | 8,937 ms | 0 / 0 | 20 / 35 ms | 167 ms / 0 |
| 100 | Baseline | 22.66 req/s | 2,172 ms | 16,847 ms | 17,169 ms | 0 / 0 | 338 / 476 ms | 2,018 ms / 20 |
| 100 | Optimized | 33.73 req/s | 326 ms | 14,617 ms | 18,422 ms | 0 / 0 | 29 / 45 ms | 291 ms / 0 |

These are not a replacement for the Phase 1 comparison: the profiler changes
timing and only one sample was taken per concurrency level. They do show that
the optimized image's event loop remains much more responsive, while
end-to-end tail latency continues to grow with authentication concurrency.
All workflow responses were the expected HTTP 200/201 statuses with zero
workflow HTTP errors, timeouts, or transport errors. Baseline lightweight
probe errors were 0/4/8/20 at 10/25/50/100 users; the optimized probe had zero
errors at every level. The runner's request timeout remained 30 seconds.

## 50-user repeat and conclusion

Four fresh paired runs are summarized in
[50_USER_REGRESSION_ANALYSIS.md](./50_USER_REGRESSION_ANALYSIS.md). Median
throughput rose from 21.38 to 34.13 requests/second and p50 fell from 1.25 s
to 0.17 s. Median p95 fell from 8.45 s to 7.72 s; median p99 rose from 8.73 s
to 9.20 s. No workflow errors or timeouts occurred. The Phase 1 p95 regression
was therefore not reproduced, and its statistical significance is
undemonstrated.

## Confirmed and unresolved items

1. **Confirmed — serialized password-executor queue.** At 50 users, the
   optimized run had one password worker, a queue high-water mark of 49, and
   queue-wait p95 of 9.61 s. PBKDF2 hash computation p95 was 201 ms and
   verification p95 was 281 ms. Endpoint p95 was 6.78 s for signup and 9.99 s
   for login. Details are in
   [PERFORMANCE_PROFILING_REPORT.md](./PERFORMANCE_PROFILING_REPORT.md).
2. **Confirmed — synchronous baseline work starved the event loop.** At 50
   users, baseline event-loop lag p95/p99 was 334/473 ms versus 20/35 ms
   optimized. At 100 users it was 338/476 ms versus 29/45 ms. This agrees
   with the baseline's async routes performing synchronous database/password
   work and the optimized boundary changes. It does not by itself prove all
   latency sources were removed.
3. **Not supported as primary causes — database pool, SQL, and Redis server.**
   At 50 users pool checkout p95 was below 0.1 ms in both final diagnostic
   runs; measured SQL statement p95 was at most 26 ms. Redis `EVAL` server
   time averaged 55 microseconds in the optimized diagnostic. The application
   Redis-call timer was 22.7 ms p95 and includes client/loop scheduling, so it
   should not be read as server execution time.
4. **Not established — pose CPU, real camera/video cost, Nginx/middleware
   fraction, and detailed Python CPU hotspots.** The harness supplies one
   uniform pose frame; no representative video payload or per-stage pose
   profile was taken. Python sampling/cProfile was unavailable, so measured
   function wall times and container CPU are not an instruction-level profile.
5. **No observed memory/GC pressure.** The 50-user sampled backend memory
   maximum was about 111 MiB baseline and 106 MiB optimized, far below the
   1-GiB limit. GC counts were collected, but pause durations were not.

## Next step

Review the evidence-ranked,
[PERFORMANCE_OPTIMIZATION_PROPOSAL.md](./PERFORMANCE_OPTIMIZATION_PROPOSAL.md)
before making changes. No optimization was implemented during Phase 2.
