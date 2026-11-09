# Performance Optimization Proposal

Status: investigation proposal only. No changes proposed here have been
implemented. Authentication security requirements remain fixed: keep PBKDF2
at 100,000 iterations, preserve bcrypt/PBKDF2 verification compatibility,
15-minute access tokens, refresh rotation/replay rejection, logout revocation,
and legacy JWT compatibility.

## Ranked proposals

| Rank | Evidence and root cause | Proposed investigation/solution | Expected benefit | Risks and security implications | Validation |
|---:|---|---|---|---|---|
| 1 | **Confirmed: serialized password executor queue.** At 50 users: one worker, queue high-water 49, queue-wait p95 9.61 s; hash compute p95 201 ms, verification 281 ms; login p95 9.99 s. At 2 CPUs, backend sampled up to 208% CPU. | Benchmark a small, controlled password-worker matrix (starting with one versus two workers) while keeping PBKDF2 cost, verification, JWT lifecycle, and admission controls unchanged. Measure queue wait and CPU saturation. Separately test a deliberately bounded backlog/admission policy so accepted auth work does not sit in a long queue; retain explicit overload behavior. | Reduce signup/login queue delay and improve high-concurrency tail if CPU capacity allows. | Additional workers may saturate the 2-CPU budget and worsen unrelated APIs. Too-small admission bounds can increase explicit 503s; too-large bounds reintroduce long waits and permit resource exhaustion. Do not remove bounds, weaken password hashing, or silently accept work. | Fresh DB/Redis images; randomized repeated 10/25/50/100 profiles; same rate limits/timeouts; report executor queue wait, accepted/rejected auth requests, event-loop lag, CPU, throughput and p95/p99. Include 50-user repeats and an auth-only stress mix. |
| 2 | **Confirmed but improved: baseline event-loop blocking.** At 50 users lag p95/p99 was 334/473 ms baseline versus 20/35 ms optimized. Optimized lag at 100 users remained 29/45 ms. | Preserve the current async/sync boundaries. Add a repeatable, lower-overhead event-loop-lag regression check to the benchmark and verify any rank-1 change does not regress the loop. | Guard against reintroducing request starvation while changing auth capacity. | Instrumentation adds overhead; benchmark-only counters must not become exposed production endpoints. | Compare instrumented and uninstrumented runs; assert reportable lag distributions, not just health-check success. |
| 3 | **Unresolved: pose CPU under real inputs.** Synthetic single-frame analysis p95 was 358 ms at 50 users; real camera/video frame size and temporal workloads were not tested. | Collect representative, consented multi-frame inputs and instrument decode, landmark preparation, feature extraction, inference, and response construction separately before optimizing. | Could expose a second CPU bottleneck for the core coaching workflow. | Model changes can alter coaching correctness; large uploads/frames can create memory/DoS risk. Keep input bounds and validate model quality. | Isolated representative workloads; per-stage CPU/wall/memory; correct output checks and model-accuracy regression gates. |
| 4 | **Low likelihood as primary cause: database pool/query time.** Pool checkout p95 was under 0.1 ms; statement p95 was at most 26 ms in the optimized 50-user profile. | Do not tune pool size yet. If future profiles show material query/checkout latency, enable and verify `pg_stat_statements`, sample pool occupancy during load, and inspect plans for the specific slow SQL. | Avoid speculative pool changes; pursue only if new evidence identifies a DB bottleneck. | Larger pools increase database connection pressure; query-level logging may expose sensitive values if configured unsafely. | Fresh DB with `pg_stat_statements`, active/idle/lock sampling, query plans without secrets, pool wait distributions. |
| 5 | **Low likelihood as primary cause: Redis server execution.** `EVAL` averaged 55 μs and `INCR` 8 μs server-side; app-side limiter p95 includes network/event-loop delay. | Keep Redis design unchanged unless a client-only timing experiment separates connection acquisition, command RTT, and event-loop scheduling. | Could remove a small per-request cost if client overhead is verified. | Avoid disabling distributed rate limiting or using process-local fallback as a performance shortcut. | Record Redis server command time and client RTT concurrently; test normal Redis health and explicit outage behavior in isolation. |
| 6 | **No observed memory/GC pressure; Nginx fraction unisolated.** Backend sampled memory was at most about 111 MiB of 1 GiB; GC counts were modest but pause time was not measured. | Defer memory/GC/Nginx tuning. Collect full-duration resource samples and isolate Nginx only if user-visible latency remains after auth-queue work. | Prevents unrelated changes and retains a clear causal chain. | Sampling/benchmarks can skew results; do not change resource limits to mask a regression. | Full-run container/cgroup sampling, GC pause instrumentation, and matched direct-backend-versus-Nginx tests. |

## Recommended sequence

1. Review and approve the investigation; this is the current stopping point.
2. Build an isolated experimental image for the bounded worker/admission
   matrix only. Do not modify the retained deployment.
3. Run randomized, fresh-image paired benchmarks with repeated 50-user trials
   and the full 10/25/50/100 profile; include auth queue and CPU measurements.
4. Run all auth/security regression tests and review overload responses,
   replay handling, logout revocation, password compatibility, and legacy JWT
   behavior.
5. Only after those results, decide whether to test representative pose/video
   profiling or database/Redis follow-up.

Do not treat the current throughput gain or the four-repeat 50-user result as a
production performance pass. The 100-user p95 remains 14.62 seconds in the
instrumented profile, and the 50-user login p95 remains about 10 seconds.
