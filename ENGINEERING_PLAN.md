# Performance Optimization Engineering Plan

Assessment date: 2026-11-09. This plan covers local, isolated validation only.

## Workflow availability

GStack is not installed in the current environment, and Claude Code has no
registered GStack slash commands. Bun is also unavailable. This work is being
performed in the Copilot session, which cannot invoke Claude Code slash
commands. The requested specialist stages therefore used documented,
reproducible repository inspection, tests, security checks, and API validation;
no project source was sent to a third-party model.

## Guardrails

- Keep the retained `pocketcoach-check` services and database volume untouched.
- Preserve existing uncommitted work; do not commit, push, merge, or deploy.
- Keep PBKDF2 at 100,000 iterations and preserve bcrypt/PBKDF2 verification.
- Preserve 15-minute access JWTs, refresh rotation/replay rejection, logout
  revocation, and legacy JWT acceptance.
- Retire access-token-only renewal on the legacy `/api/auth/refresh` route;
  that contract bypassed refresh-token rotation and could extend a stolen
  access JWT indefinitely. Both refresh routes now use rotating refresh tokens.
- Do not tune rate limits or benchmark resources differently between baseline
  and optimized runs.

## Plan

1. **Validate the measurement harness and baseline.**
   - Verify the benchmark sends bearer credentials and records endpoint-level
     HTTP failures separately from transport timeouts.
   - Run the unchanged verification image in a fresh isolated Compose project
     with synthetic data at 10, 25, 50, and 100 concurrent users.
   - Record p50/p95/p99, throughput, status counts, timeouts, container CPU
     and memory, PostgreSQL connection/query activity, and Redis availability.
   - Treat existing benchmark files as historical until they are reproduced;
     previous artifacts disagree on the 10–100-user rates.
2. **Implement only evidence-backed execution-boundary changes.**
   - Keep synchronous SQLAlchemy work and CPU-heavy pose analysis out of the
     ASGI event loop by using FastAPI's synchronous route execution.
   - Dispatch password hashing/verification to a dedicated, bounded executor;
     keep the existing algorithms, iteration count, hash format, and
     verification behavior. Reject excess in-flight hash work explicitly
     rather than creating an unbounded executor queue.
   - Do not change database schema, worker count, token lifecycle, or auth
     architecture.
3. **Test and review.**
   - Add regression coverage for hash compatibility, bounded admission,
     503 overload behavior, authentication flows, and token lifecycle.
   - Run the focused suite, full backend suite, compilation, and static checks.
   - Review async boundaries, thread/session behavior, overload handling,
     sensitive logging, and resource lifecycle.
4. **Benchmark and QA.**
   - Build a separate optimized image and run the same isolated profiles with
     the same resources, fresh databases, rate limits, test script, and
     timeout settings.
   - Compare measured results without omitting errors or failed requests.
   - Exercise signup, login, profile, adaptive training, session create/list,
     analysis, refresh rotation, logout, error paths, and responsive frontend
     behavior without using the retained deployment.
5. **Update reports and readiness decision.**
   - Publish root-cause, optimization, security, code-review, benchmark, and QA
     evidence; retain explicit blockers if any gate remains unmet.

## GStack installation result

The official GStack README and `docs/install.md` were inspected. GStack,
registered Claude slash commands, and Bun are absent; Git, Node.js, and Claude
Code are present, but this work is running in Copilot SDK rather than Claude
Code. The official setup requires Bun and installs/updates Claude user
configuration. It was not run without Bun, and no global configuration was
modified. The requested `/plan-eng-review`, `/investigate`, `/cso`, `/review`,
`/benchmark`, and `/qa` stages were represented by this plan, evidence-based
investigation, targeted internal security/code review, matched synthetic
benchmarks, and API regression workflows; they were not executed as GStack
slash commands.

## Execution outcome

- The final clean comparison used fresh PostgreSQL/Redis projects, the same
  2-CPU/1-worker limits, and a backend responsiveness probe through Nginx.
  At 100 users, throughput improved from 15.79 to 31.84 requests/second and
  p95 from 23.47 to 16.65 seconds. At 25 users, the baseline recorded 47
  timeouts and the optimized run recorded none; at 50 users p95 regressed.
- The full backend regression suite passed with Redis 8 enabled: 118 passed,
  zero skipped. Isolated API QA passed signup/login, profile, adaptive
  training, sessions, analysis, refresh rotation/replay, and logout revocation.
- The optimized high-concurrency performance gate remains **FAIL**. The
  application is not production-ready. Direct asyncio lag instrumentation,
  browser-driven/responsive UI checks, physical-device testing, and
  production-like soak/capacity testing remain incomplete.
