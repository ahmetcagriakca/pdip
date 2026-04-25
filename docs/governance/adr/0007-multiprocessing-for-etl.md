# ADR-0007: Use `multiprocessing` (not `asyncio`) for ETL parallelism

- **Status:** Accepted (partially superseded by [ADR-0032](./0032-hybrid-async-strategy.md))
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** integrator, concurrency

> **Note (2026-04-25):** [ADR-0032](./0032-hybrid-async-strategy.md)
> partially supersedes this ADR. Multiprocessing remains the default
> ETL parallelism primitive and the pandas/CPU-bound rationale below
> still holds. The "asyncio is rejected" conclusion in
> *Alternatives considered → Option A* is replaced by "asyncio is
> available as an additive, opt-in execution strategy under the
> `pdip[async]` extra"; everything else in this ADR stands.

## Context

pdip moves data between relational databases, message queues (Kafka),
files, and web services. The hot path is a batched pipeline that reads
from a source, transforms, and writes to a target. The limiting resource
is usually either the target's write throughput or the client library's
ability to convert rows (pandas, pyodbc, cx_Oracle, psycopg2,
mysql-connector).

Python gives us three realistic options for parallelism:

- Threads (limited by the GIL for CPU-bound work; acceptable for
  I/O-bound work but client libraries vary in their thread-safety).
- `asyncio` (requires async-native drivers for every backend we support,
  several of which have no production-ready async client).
- Processes (bypass the GIL entirely; each worker has its own
  interpreter, imports, and client connections).

## Decision

The integrator uses Python's `multiprocessing` as its parallelism
primitive. `pdip/processing/` wraps this into:

- `ProcessManager` — owns the lifecycle of a pool of worker processes
  and distributes tasks over a queue.
- `Subprocess` — the worker base class. On startup it re-initialises
  the DI container in the child process (see ADR-0001 and
  [ADR-0015](./0015-service-auto-discovery.md)) so injected services
  exist in each worker.

Integration steps can be executed single-process, parallel-thread, or
parallel-process (the strategies live under
`pdip/integrator/integration/types/`); the parallel-process variant is
the default for throughput.

## Consequences

### Positive

- CPU-bound transformation (pandas in particular) scales across cores
  instead of being stuck on the GIL.
- Client libraries that are not thread-safe (`cx_Oracle`,
  `mysql-connector`) are safe because each worker owns its own
  connection.
- The process boundary also provides fault isolation: a segfault in a
  native driver takes down one worker, not the whole job.

### Negative

- Every object passed to a worker must be picklable. Closures,
  lambdas, and objects that reference open file descriptors cannot be
  shipped across the boundary.
- Workers must rehydrate the DI container on startup, which adds a
  small per-worker latency.
- Cross-process eventing required the message broker in
  [ADR-0006](./0006-pubsub-message-broker.md).

### Neutral

- On Windows, `multiprocessing` uses `spawn`, which re-imports modules
  in the child. Any module-level side effect must be idempotent. This
  constrains how the framework initialises itself.

## Alternatives considered

### Option A — `asyncio`

- **Pro:** Lightweight; great for I/O-bound fan-out.
- **Con:** Requires async-native drivers for every backend we support.
  pyodbc, cx_Oracle, and several BigData clients have no production-
  ready async equivalent. Mixing sync drivers with asyncio defeats the
  purpose.
- **Why rejected:** The integration surface is too sync-heavy for
  asyncio to pay off.

### Option B — Threads (`concurrent.futures.ThreadPoolExecutor`)

- **Pro:** Cheap, well-understood, good for I/O.
- **Con:** The GIL caps pandas/arrow transforms at one core; a subset
  of our drivers is not thread-safe.
- **Why rejected:** Kept as an optional execution strategy for
  I/O-dominated integrations, but not as the default.

### Option C — Celery or another task queue

- **Pro:** Distributes beyond one host.
- **Con:** Requires a broker (Redis/RabbitMQ) and adds ops burden.
- **Why rejected:** Out of scope for the in-process framework; users
  who need distribution can wrap pdip in their own task queue.

## Follow-ups

- Document the "picklability" rule for data passed across the process
  boundary in the contributor guide.
- Revisit when `asyncio`-native drivers for the full backend matrix
  become production-ready.

## References

- Code: `pdip/processing/base/process_manager.py`,
  `pdip/processing/base/subprocess.py`,
  `pdip/integrator/integration/types/`
