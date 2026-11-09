# Performance and Model Report

Status: low-volume API and authenticated synthetic workflow samples were
completed locally by 2026-11-09. These measurements are not a capacity or
production-performance certification.

## API load sample

The sample used the Nginx endpoint `GET /api/adaptive/capabilities` with the
backend, PostgreSQL, Redis, and Nginx containers running. The client and stack
were on the same host (`127.0.0.1`). Ten warm-up requests preceded 50 measured
requests at concurrency 10. Percentiles use the nearest-rank method.

| Measurement | Result |
|---|---:|
| Measured requests | 50 |
| Concurrency | 10 |
| HTTP 200 / errors | 50 / 0 |
| Elapsed time | 0.430 s |
| Throughput | 116.33 requests/s |
| p50 latency | 80.48 ms |
| p95 latency | 92.87 ms |
| p99 latency | 93.44 ms |
| Maximum latency | 93.44 ms |

This is one short, loopback sample against a lightweight capabilities endpoint.
It includes Nginx and application middleware, including the live Redis-backed
rate limiter, but does not measure authenticated database writes, pose/video
analysis, sustained load, external network latency, or production hardware.
It is not a throughput guarantee. A broader staging test should measure
representative authenticated workflows, pose-analysis inputs, resource use,
and behavior at and beyond configured rate limits.

An earlier local health smoke sample recorded 40 sequential `GET /health`
requests: median 4.742 ms, p95 5.277 ms, maximum 129.945 ms. That sample is
also not comparable to the Compose API sample above.

## Authenticated workflow load

A synthetic end-to-end harness exercised signup, login, protected profile,
adaptive catalog, skills, session creation/history, analytics, pose analysis,
refresh, and logout through Nginx. The isolated Compose stack used synthetic
accounts and a test-only rate limit. Ten readiness requests warmed the stack.

| Concurrent users | Requests | Throughput | p50 | p95 | p99 | HTTP errors |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 120 | 14.78 req/s | 413.38 ms | 2,108.08 ms | 2,294.54 ms | 0 |
| 25 | 300 | 20.50 req/s | 747.09 ms | 4,021.52 ms | 4,677.11 ms | 0 |
| 50 | 600 | 20.20 req/s | 1,296.50 ms | 8,266.52 ms | 9,689.21 ms | 0 |
| 100 | 1,200 | 21.14 req/s | 2,525.67 ms | 17,286.82 ms | 18,002.84 ms | 0 |

Throughput plateaued near 21 requests/second while p95 grew to 17.29 seconds
at 100 users. A separate 100-user repeat with a roughly one-second container
resource sample reached about 106.96% of one CPU and 116.2 MiB backend memory;
that repeat reported 15.96 requests/second and 23.35 seconds p95 on a database
already populated with prior synthetic accounts. These measurements indicate
that zero HTTP errors do not imply acceptable interactive latency.

The load is local, synthetic, short-duration, and uses uniform pose landmarks.
It is not a sustained soak, realistic video test, or production capacity
commitment. Detailed methodology and caveats are in
[AUTHENTICATED_LOAD_TEST_REPORT.md](./AUTHENTICATED_LOAD_TEST_REPORT.md).

## Earlier fresh-image bottleneck isolation

These preliminary trials are historical context. The final clean matched
comparison below is the authoritative before/after measurement.

The fresh backend image was profiled through Nginx with synthetic accounts,
fresh PostgreSQL volumes for the 2-CPU runs, a 1 GiB backend memory cap, and a
test-only rate limit of 5,000 requests/minute. The results below supersede any
assumption that the earlier zero-error profile proves the current image can
handle 100 concurrent users.

| Backend CPU cap | Uvicorn workers | Requests | Throughput | p95 | Errors/timeouts | Peak backend CPU |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 202 | 3.35 req/s | 30.02 s | 49.01% | about 105% |
| 2 | 1 | 133 | 2.14 req/s | 30.05 s | 75.19% | 216.12% |
| 2 | 2 | 150 | 2.18 req/s | 30.07 s | 66.67% | 226.53% |

These short local profiles do not establish production capacity. The 2-CPU,
two-worker sample averaged about 145% backend CPU across nine resource samples
(peak 226.53%; peak memory 238.7 MiB). PostgreSQL reached 112.57% peak CPU,
but its busiest measured statement averaged 2.922 ms (34.477 ms maximum); the
top five statements each averaged under 8 ms. At most 20 PostgreSQL client
connections and one active query were captured. Redis command execution was
also small (`EVAL` 0.412 ms/call, `INCR` 0.016 ms/call), although Redis
connection timeouts and the application’s in-memory fallback appeared in
backend logs during saturation.

The evidence points to CPU-bound request processing and event-loop starvation,
with synchronous PBKDF2 work in the async signup/login handlers as a strong
contributor—not a slow-query or Redis-command bottleneck. A 100-hash
microbenchmark took 12.71 seconds and 100 verifications 13.47 seconds on one
CPU; an unbounded 20-thread hash benchmark took 89.34 seconds on one CPU.
Password-hash cost and token behavior were left unchanged. Raising the CPU cap
and enabling two Uvicorn workers did not improve the high-concurrency profile
enough to pass; do not deploy a worker-count change based on these results.

Two-worker startup first exposed concurrent schema initialization: both
workers ran SQLAlchemy `create_all()` and one failed with a duplicate
PostgreSQL type error. A PostgreSQL advisory lock now serializes initialization;
the isolated two-worker deployment and backend restart then passed. This
correctness fix permits a safe experiment but is not itself a performance fix.

## Final matched clean-image comparison

The final comparison used separate fresh PostgreSQL/Redis Compose projects
for the verification baseline and optimized image, run sequentially through
Nginx. Both used one Uvicorn worker, a 2-CPU backend limit, 1 GiB memory,
5,000 requests/minute test-only rate limit, 30-second client timeout, the
same synthetic workflow runner, ten readiness warm-ups, and 10/25/50/100
concurrent users. The backend responsiveness probe targeted the FastAPI
`/api/adaptive/capabilities` route through Nginx (100 ms interval, 2-second
timeout); it is a responsiveness proxy, not direct event-loop-lag
instrumentation.

| Users | Throughput, baseline → optimized | p50, baseline → optimized | p95, baseline → optimized | p99, baseline → optimized | Workflow timeouts, baseline → optimized |
|---:|---:|---:|---:|---:|---:|
| 10 | 9.30 → 25.05 req/s | 513 → 72 ms | 3,994 → 1,818 ms | 4,827 → 2,118 ms | 0 → 0 |
| 25 | 1.52 → 22.92 req/s | 3,553 → 152 ms | 30,015 → 5,610 ms | 30,028 → 8,232 ms | 47 → 0 |
| 50 | 21.51 → 25.52 req/s | 1,276 → 138 ms | 7,978 → 9,087 ms | 8,937 → 12,511 ms | 0 → 0 |
| 100 | 15.79 → 31.84 req/s | 3,652 → 186 ms | 23,470 → 16,646 ms | 26,931 → 20,791 ms | 0 → 0 |

The 100-user run approximately doubled throughput and reduced p95 by 29%,
but 16.65 seconds p95 remains unacceptable for an interactive service. At 50
users p95/p99 worsened despite higher throughput. The optimization improved
backend probe responsiveness (baseline p95 roughly 2.0 seconds with errors;
optimized p95 about 0.16–0.20 seconds with no probe errors), while sampled
backend peak CPU increased from 155.34% to 213.38% of the two-core limit and
peak memory stayed near 113 MiB. PostgreSQL peaks and connection counts were
moderate (at most 15 baseline and 11 optimized connections; at most 1 and 2
sampled active queries, respectively).

This is a matched short local workload, not a sustained soak or production
capacity test. It demonstrates that reducing event-loop blocking improves
many responses but does not remove CPU-bound password work from the end-to-end
tail. The high-concurrency performance gate remains **FAIL**; keep the
application out of public production until a production-like performance
target is met without weakening password hashing.

## Existing offline classifier evaluation

The checked-in `dataset/reports/model_comparison.json` describes a
single-image, three-way sport-folder classification task. On its 721-sample
test split, the validation-selected gradient-boosting model reported:

| Metric | Result |
|---|---:|
| Accuracy | 68.93% |
| Macro-F1 | 60.65% |
| Table Tennis F1 | 36.17% |
| Reported estimator latency | 0.0151 ms/sample |

The estimator latency is from the offline comparison and is not end-to-end
application inference latency. This dataset has no movement/technique labels
or video sequences, so these metrics do not measure coaching quality or
temporal motion recognition. The artifact remains experimental and is not
validated for live integration; the existing sport analyzers remain in use.
Do not treat 68.93% accuracy as evidence of reliable technique recognition
or coaching quality.

## Product and data priority

The local dataset audit found 30,121 files across 39 categories, including
29,814 images, no videos, and 3 annotation-extension files. These assets do
not constitute temporal movement labels. Candidate video sources in
`dataset/source_catalog.json` remain unverified or noncommercial; no external
media was acquired and no temporal model was trained. The current pipeline is
blocked on an approved, consented/rights-verified video source.

The next major product-development effort should be movement-specific,
multi-sport data and evaluation:

1. Establish consented video collection and privacy/retention controls.
2. Build an expert annotation workflow with clear movement and technique
   labels, quality review, and inter-annotator checks.
3. Extract and validate temporal pose sequences from representative video.
4. Evaluate models independently on held-out athletes/sessions and report
   per-sport, per-movement, and robustness metrics before any live integration.

Keep the current classifier experimental until this data and evaluation
foundation supports a defensible quality claim. After production-readiness
gates, use a controlled real-athlete pilot to validate product behavior and
collect consented feedback/data; do not jump directly to public launch.

## Additional operational measurement

Once higher-priority PostgreSQL upgrade, backup/restore, production
configuration, monitoring, and independent security checks are complete, run
broader authenticated staging tests. Measure endpoint-specific latency and
errors, pose-analysis throughput, CPU/memory, and rate-limit behavior at
declared concurrency. Use realistic browser video/device inputs and record
hardware, dataset, environment, warm-up, sample size, and p50/p95/p99
thresholds.
