# Root-Cause Investigation: High-Concurrency API Latency

Assessment date: 2026-11-09. All new measurements used a synthetic, isolated
Compose project; the retained deployment and database volume were not used.

## Reproduced baseline

The original one-CPU results below are retained as an earlier reference. The
final decision uses the clean, matched two-CPU comparison later in this
document.

The pre-optimization image
`pocketcoach-backend:verification-20261108-init-lock` was exercised through
Nginx with a fresh PostgreSQL volume, Redis 8, one Uvicorn worker, a 1-CPU
backend limit, a 5,000-requests/minute test-only rate limit, and 10 readiness
warm-ups. The authenticated workflow ran at 10, 25, 50, and 100 concurrent
users; each virtual user attempts 12 workflow requests, for up to 1,200
requests at the 100-user profile.

| Users | Requests | Elapsed | Throughput | p50 | p95 | p99 | HTTP/transport errors |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 120 | 6.890 s | 17.42 req/s | 290.57 ms | 2,014.52 ms | 2,676.36 ms | 0 |
| 25 | 300 | 17.478 s | 17.16 req/s | 806.03 ms | 6,257.92 ms | 6,522.98 ms | 0 |
| 50 | 600 | 28.050 s | 21.39 req/s | 1,212.61 ms | 7,794.40 ms | 8,492.11 ms | 0 |
| 100 | 1,200 | 60.775 s | 19.74 req/s | 2,430.64 ms | 19,683.40 ms | 20,742.25 ms | 0 |

At 100 users, endpoint p95 was 19.32 s for signup, 20.87 s for login, and
16.42 s for authenticated profile. The remaining workflow endpoints ranged
from 1.41 s for adaptive profile to 3.66 s for pose analysis. Thus the
interactive performance gate failed even in a run with no HTTP errors.

## Evidence and causal assessment

1. **Synchronous password hashing blocks async request handling (primary).**
   Signup and login were `async` FastAPI routes but called synchronous
   PBKDF2/bcrypt code directly. Each 100,000-iteration PBKDF2 operation
   therefore occupied the event-loop thread. A prior isolated microbenchmark
   measured 100 hashes in 12.71 s and 100 verifications in 13.47 s on one CPU.
   The observed signup/login tail latency is consistent with that CPU-bound
   work serializing unrelated coroutine progress.
2. **Other synchronous work also ran in async route handlers (secondary).**
   SQLAlchemy queries/commits and pose-analysis computation are synchronous.
   Several handlers had no `await` at all, so their declarations did not make
   that work non-blocking. They can add event-loop stalls under concurrent
   authenticated traffic.
3. **Backend CPU, not memory, was the constrained resource in the sampled
   baseline.** The 1-CPU backend reached 101.88% sampled CPU and 115.9 MiB
   memory. PostgreSQL, Redis, and Nginx sampled peaks were 47.43%/60.8 MiB,
   24.29%/9.9 MiB, and 10.26%/5.4 MiB respectively. The sampler captured only
   35 seconds of the 113-second run, so these are observed samples, not
   guaranteed full-run peaks.
4. **Database/Redis service time was not a primary explanation.** The
   synthetic PostgreSQL query statistics showed mean execution times below
   1 ms for the busiest application statements. Redis processed about 4,523
   commands with zero rejected connections, and no Redis error was found in
   the baseline backend logs. Earlier isolated measurements also found low
   Redis command times. Redis connection timeouts were present in a separate,
   more severe historical saturation run and remain a resilience concern,
   not evidence that Redis command execution caused this baseline.
5. **More CPU/workers alone were not a reliable fix.** Earlier fresh-image
   profiles at 2 CPUs and at two workers still reached roughly 30-second p95
   and high client timeout rates. This investigation keeps the default worker
   count and password work factor unchanged.

Historical saved profiles vary materially: some report 49–75% client
timeouts at 100 users, while other saved runs show zero HTTP errors and
different throughput. The reproducible run above is the before measurement
for this optimization; historical data is retained as context, not mixed into
the before/after comparison.

## Final clean matched comparison

The verification baseline and optimized image were run sequentially through
Nginx in separate new Compose projects, each with a fresh PostgreSQL volume
and Redis 8 service. Both used one Uvicorn worker, a 2-CPU/1-GiB backend
limit, 5,000 requests/minute test-only rate limit, 30-second workflow timeout,
ten readiness warm-ups, identical synthetic workflows, and 10/25/50/100 user
profiles. A 100-ms backend responsiveness probe targeted
`/api/adaptive/capabilities` with a 2-second timeout.

| Users | Baseline p95 / throughput | Optimized p95 / throughput | Baseline workflow timeouts | Backend probe p95/errors, baseline → optimized |
|---:|---:|---:|---:|---:|
| 10 | 3.99 s / 9.30 req/s | 1.82 s / 25.05 req/s | 0 | 2.02 s / 2 → 0.18 s / 0 |
| 25 | 30.01 s / 1.52 req/s | 5.61 s / 22.92 req/s | 47 | 2.02 s / 47 → 0.20 s / 0 |
| 50 | 7.98 s / 21.51 req/s | 9.09 s / 25.52 req/s | 0 | 2.02 s / 8 → 0.16 s / 0 |
| 100 | 23.47 s / 15.79 req/s | 16.65 s / 31.84 req/s | 0 | 2.03 s / 33 → 0.20 s / 0 |

No HTTP error response was recorded in the workflows. Client timeouts
accounted for the baseline failures. The baseline backend's three-second
readiness check also timed out repeatedly and Docker temporarily marked the
container unhealthy under load; the container remained running and the
failure was a readiness timeout, not an observed process exit. The optimized
backend stayed healthy in the matched run.

At 100 users, the optimized image roughly doubled throughput and reduced p95
by 29%, but 16.65 seconds p95 still fails the interactive performance gate.
At 50 users p95/p99 worsened, despite lower median latency and higher
throughput. Backend CPU peaked at 155.34% of the two-CPU cap before and
213.38% after; peak memory was 117.0 and 113.3 MiB. Sampled PostgreSQL
connections peaked at 15 and 11, and active queries at 1 and 2. The samples
do not indicate connection exhaustion or slow queries as the dominant cause.
Redis was healthy during startup, but final-run Redis command latency was not
instrumented.

## Limitations

The benchmark records per-endpoint HTTP latency, throughput, status codes,
transport timeouts, container CPU/memory, sampled PostgreSQL activity, and
latency/errors for a lightweight backend endpoint. It does not directly sample
asyncio event-loop scheduling lag. Synthetic one-frame pose data also does not
represent live camera/video throughput.

## Conclusion

The evidence supports moving CPU-bound password work off the ASGI event loop
with bounded admission, and running synchronous database/pose handlers via
FastAPI's synchronous route execution. These changes materially improve
backend responsiveness and median latency, but the optimized 100-user p95
remains 16.65 seconds and the 50-user p95 regressed. Do not lower the
password-hashing work factor, tune connection pools, or increase production
worker counts without further evidence and a passing production-like test.

## Phase 2 profiling update (2026-11-09)

The previous statement that direct event-loop lag was not measured applies to
the Phase 1 benchmark. Phase 2 added isolated 10-ms loop-lag, SQLAlchemy pool
and statement, Redis limiter, password executor, GC, and thread-state
instrumentation. The retained `pocketcoach-check` deployment and its database
volume were not used.

The optimized code materially reduced baseline event-loop lag. At 50 users,
the four-repeat baseline/optimized comparison had median p95 workflow latency
of 8.447/7.719 seconds and median p99 of 8.729/9.198 seconds. The Phase 1
single-run p95 regression did not recur; four samples do not establish formal
statistical significance.

The leading remaining cause is now directly measured password-executor
queueing, not an unverified assumption about PBKDF2 alone. In the optimized
50-user diagnostic, the dedicated executor had one worker and a queue maximum
of 49; queue-wait p95 was 9.606 seconds. PBKDF2 hash and verification
computation p95 were about 201 and 281 ms, respectively. Signup and login
endpoint p95 were 6.778 and 9.993 seconds. At the same concurrency,
event-loop-lag p95/p99 was 20/35 ms, the SQLAlchemy pool checkout p95 was
0.092 ms, SQL statement p95 was at most 25.912 ms, and Redis `EVAL` server
execution averaged 54.83 microseconds. The latter observations do not support
database pool wait or Redis command execution as the primary multi-second
tail cause.

The instrumented 10/25/50/100 profile had optimized p95 values of
1.498/3.580/7.066/14.617 seconds and zero workflow errors/timeouts. The
100-user performance gate remains failed. Profiling limitations include no
instruction-level Python CPU profile (Pylance Tachyon requires Python
3.15.0b3+, while the selected host is 3.14.2), one-frame pose inputs, and
short/partial Docker resource samples. PostgreSQL `pg_stat_statements` was not
available in the test database. GStack was not installed or invoked.

The worktree and historical Phase 1 reports remain preserved. See
[PHASE2_PERFORMANCE_INVESTIGATION.md](./PHASE2_PERFORMANCE_INVESTIGATION.md),
[PERFORMANCE_PROFILING_REPORT.md](./PERFORMANCE_PROFILING_REPORT.md),
[50_USER_REGRESSION_ANALYSIS.md](./50_USER_REGRESSION_ANALYSIS.md), and
[PERFORMANCE_OPTIMIZATION_PROPOSAL.md](./PERFORMANCE_OPTIMIZATION_PROPOSAL.md)
for methodology, repeated samples, limitations, and the evidence-ranked
proposal. No proposed optimization has been implemented.
