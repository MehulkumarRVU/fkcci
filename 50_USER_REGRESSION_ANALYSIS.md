# 50-User Regression Analysis

Assessment date: 2026-11-09. This analysis investigates the single-run Phase 1
observation that p95 worsened from 7.98 seconds to 9.09 seconds after
optimization.

## Matched repeats

Four paired comparisons were run with fresh isolated PostgreSQL and Redis
projects for each pair. The baseline and optimized images each received one
50-user, 600-request workflow per pair. Run order alternated for the first
three pairs; the fourth was an additional diagnostic run with password-queue
and Docker-resource instrumentation. Both images used 2 backend CPUs, one
Uvicorn worker, 1 GiB backend memory, the same test-only rate limit, runner,
timeout, and responsiveness probe. No workflow errors or timeouts occurred.

| Pair | Run order | Baseline throughput | Baseline p50 / p95 / p99 | Optimized throughput | Optimized p50 / p95 / p99 |
|---:|---|---:|---:|---:|---:|
| 1 | Baseline then optimized | 22.00 req/s | 1,182 / 8,218 / 8,662 ms | 35.02 req/s | 147 / 7,897 / 9,016 ms |
| 2 | Optimized then baseline | 20.81 req/s | 1,234 / 8,767 / 9,164 ms | 34.89 req/s | 176 / 7,209 / 8,633 ms |
| 3 | Baseline then optimized | 21.55 req/s | 1,296 / 8,421 / 8,684 ms | 33.37 req/s | 170 / 7,739 / 9,379 ms |
| 4 | Baseline then optimized | 21.20 req/s | 1,275 / 8,472 / 8,775 ms | 32.09 req/s | 218 / 7,700 / 9,909 ms |
| **Median** | — | **21.38 req/s** | **1,255 / 8,447 / 8,729 ms** | **34.13 req/s** | **173 / 7,719 / 9,198 ms** |

Across these four samples, optimized p95 was 8.6% lower by the paired-image
medians and ranged from 7.21–7.90 seconds, versus 8.22–8.77 seconds baseline.
Optimized p99 median was 5.4% higher (9.20 versus 8.73 seconds). Throughput
was 59.7% higher by the medians; p50 was substantially lower.

## Event-loop and auth evidence

The three instrumented pairs with the corrected event-loop sampler recorded
baseline event-loop lag p95 around 316–341 ms and optimized p95 around
17–19 ms. The fourth pair recorded 326 ms baseline and 20 ms optimized. The
lightweight endpoint probe similarly remained around 2.02 seconds p95 on
baseline, versus approximately 139–164 ms on optimized.

The fourth optimized pair measured one password worker, executor queue depth
up to 49, and queue-wait p95 of 9.61 seconds. Hash computation p95 was 201 ms;
verification computation p95 was 281 ms. Signup p95 was 6.78 seconds and login
p95 was 9.99 seconds. Non-authenticated-cost endpoints in that synthetic
workflow were generally hundreds of milliseconds at p95, not several seconds.
This identifies authentication work queueing as the leading tail source,
not the original event-loop stall alone.

## Assessment

The Phase 1 single-run p95 regression did **not** recur in these four paired
fresh-project runs. This is evidence against treating the original 50-user
p95 increase as a stable regression. It is not a formal test of statistical
significance: four pairs are too few to estimate tail variability confidently,
and the Phase 2 wrapper adds instrumentation overhead. The slightly higher
optimized p99 median also means the optimized tail is not uniformly better.

Likely contributors to the original one-run difference include normal
run-to-run tail variability, single-sample ordering/resource contention, and
the optimized design moving password work off the event loop into a single
worker queue. The latter is a confirmed bottleneck at 50 users; it can keep
auth requests slow while making lightweight endpoints much more responsive.
The current evidence cannot apportion the original p95 difference among those
factors.

## Conclusion

Record the Phase 1 50-user result as a one-run observed p95/p99 regression,
not a statistically established regression. The controlled Phase 2 repeats
show lower median p95 but slightly higher median p99. Keep the 50-user
performance gate open until an uninstrumented, randomized, adequately repeated
benchmark confirms the full latency distribution under identical fresh-image
conditions.
