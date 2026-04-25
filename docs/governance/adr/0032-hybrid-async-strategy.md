# ADR-0032: Hybrid async strategy via additive `pdip[async]` extra

- **Status:** Proposed
- **Date:** 2026-04-25
- **Deciders:** pdip maintainers
- **Tags:** integrator, concurrency, packaging, async
- **Partially supersedes:** [ADR-0007](./0007-multiprocessing-for-etl.md)
  (multiprocessing remains the default; this ADR adds an alternative,
  it does not remove the existing one)

## Context

[ADR-0007](./0007-multiprocessing-for-etl.md) committed pdip to
`multiprocessing` as the parallelism primitive for ETL because:

- Many of our backend client libraries (`cx_Oracle`,
  `mysql-connector`, `pyodbc`) had no production-ready async
  equivalent.
- Pandas-heavy transforms are CPU-bound and benefit from real OS
  processes that bypass the GIL.

Three things have shifted since that decision was first written:

- The drivers landscape moved. `oracledb` (ADR-0021) ships an
  async API. `asyncpg` is the default for PostgreSQL in async
  workloads. `aiomysql` and `aiokafka` are mature. `aioodbc` covers
  pyodbc-style drivers. The "no async drivers" leg of ADR-0007 is
  no longer load-bearing for the SQL connectors and Kafka.
- Many production deployments of pdip are not pandas-heavy ETL;
  they are I/O-bound integrations (REST → Postgres, Kafka →
  Postgres, file → Postgres) where the GIL is not the bottleneck
  and one process with hundreds of in-flight coroutines beats N
  processes with one connection each.
- ADR-0034 is queueing 1.0. Locking ourselves out of async in
  perpetuity at 1.0 would be hard to reverse.

We do *not* want to rewrite the existing sync API as async. That
would be a 12-month project, would invalidate every existing
integration, and would force every user to rewrite. The pandas
case from ADR-0007 is real: a worker doing heavy transforms in
pandas inside an `async def` is just a single core blocked on the
GIL.

## Decision

### 1. Async is additive, sync stays the default

We add async as a *parallel* execution path. Every existing public
class, factory, and integrator entry point keeps its current
synchronous signature. The current `multiprocessing`-based
`ParallelIntegrationExecute` and the thread-based
`ParallelThreadIntegrationExecute` under
`pdip/integrator/integration/types/sourcetotarget/strategies/` stay
exactly as they are. ADR-0007 is **partially superseded**: the
"asyncio is rejected" conclusion is replaced by "asyncio is
optional and additive"; the rest of ADR-0007 (process model,
DI rehydration in workers, picklability rule) stands.

### 2. New optional extra: `pdip[async]`

The async path is gated behind a new extra in `setup.py`. It pulls:

- `oracledb[async]` (already a dependency of `pdip[integrator]`,
  the `[async]` tag enables the async API path).
- `asyncpg`.
- `aiomysql`.
- `aioodbc`.
- `aiokafka`.

Framework code never imports any of these at module top-level —
imports are local to the async-strategy module and the async
adapter classes, mirroring the lazy-import pattern from ADR-0014.

### 3. Async sibling adapters, not async-everything

Each existing connector keeps its synchronous `ConnectionSourceAdapter`
/ `ConnectionTargetAdapter` subclass. Async support is added by a
**sibling** class with an `Async` prefix that lives next to the sync
one — for example, `pdip/integrator/connection/types/sql/postgres/`
gets an `AsyncPostgresSourceAdapter` next to the existing
`PostgresSourceAdapter`. The sync class is unchanged; the async
class implements an async variant of the adapter protocol whose
methods are `async def`.

Two new abstract bases land alongside the existing ones in
`pdip/integrator/connection/base/`:

- `AsyncConnectionSourceAdapter` (async sibling of
  `ConnectionSourceAdapter`).
- `AsyncConnectionTargetAdapter` (async sibling of
  `ConnectionTargetAdapter`).

The factories
(`pdip/integrator/connection/factories/connection_source_adapter_factory.py`,
`pdip/integrator/connection/factories/connection_target_adapter_factory.py`)
gain an `is_async: bool = False` parameter; when `True`, they return
the async sibling. When the `pdip[async]` extra is not installed and
the caller asks for `is_async=True`, the factory raises a clear
`ImportError` ("install `pdip[async]` to use async adapters")
*synchronously*, before the integration starts.

### 4. New execution strategy: `AsyncIntegrationExecute`

We add a fourth execution strategy under
`pdip/integrator/integration/types/sourcetotarget/strategies/async_/`
next to the existing `singleprocess/`, `parallelthread/`, and
`parallelold/` directories. It runs the integration inside an
`asyncio.run`, fans out reads/writes via `asyncio.gather` with a
configurable concurrency cap, and uses the async sibling adapters
from §3.

`IntegrationSourceToTargetExecuteStrategyFactory` learns a new
`async` strategy name. Configuration mirrors the existing pattern:
the strategy is selected through the integration's YAML/JSON
descriptor, defaulting to the existing parallel-process strategy.

### 5. ADR-0007's pandas case is preserved

The async strategy is **only** wired through I/O-bound adapter
calls. CPU-bound transforms continue to live where they live today
(in the same worker that read the rows). Users with a pandas-heavy
transformation pipeline pick the existing `parallelold` strategy
and pay the multiprocessing cost ADR-0007 already justifies. The
selection is a configuration decision per integration, not a
framework-wide switch.

This is why we are not "moving to async": for a meaningful slice of
real workloads, multiprocessing is still the right answer.

### 6. Cross-cutting concerns

- **Pub/sub broker** (`pdip/integrator/pubsub/base/message_broker.py`,
  `event_listener.py`): the broker stays thread-based. Async
  strategies bridge to it through `loop.run_in_executor` for the
  publish path; the listener side is untouched. We do not introduce
  a second broker.
- **Observability**: spans and metrics for the async path use the
  same names defined in [ADR-0033](./0033-opentelemetry-observability.md)
  with `pdip.step.strategy = "async"`. No new span vocabulary.
- **DI / `injector`**: the async strategy reuses the existing
  container; async-handler resolution does not require a separate
  injector. Service classes consumed by async adapters can mix sync
  and async methods on the same class — only the call sites that
  perform I/O are `async def`.
- **Public API under ADR-0034**: `AsyncConnectionSourceAdapter`,
  `AsyncConnectionTargetAdapter`, the new `async` strategy name,
  and the factory `is_async` flag enter the public surface during
  the 1.0 audit.

### 7. Documentation and migration

- README install table gains an `async` row alongside `api`,
  `cryptography`, `integrator`.
- `docs/async.md` (new) explains: when to pick async over the
  parallel-process strategy, the I/O-vs-CPU rule of thumb, and the
  list of connectors with async siblings shipped versus deferred.
- ADR-0007 gets a header note pointing to this ADR; its body is
  unchanged.

## Consequences

### Positive

- I/O-bound integrations get a dramatic throughput improvement
  without paying the per-worker process cost.
- Each connector adopts async on its own schedule — adding an
  async sibling for a new backend does not block on the others.
- The existing sync API is unchanged. Every existing user
  upgrades to the version that ships `pdip[async]` without
  changing a line of their integrations.

### Negative

- The connector matrix doubles in shape: every backend has a sync
  adapter and a (possibly absent) async sibling. Documentation has
  to be explicit about which adapters have async coverage.
- Two execution paths, two test matrices. ADR-0027's diff-cover
  applies to both.
- An integration that mixes a sync source and an async target (or
  vice versa) is not supported in the first cut; the strategy
  picks one mode per integration. Mixed-mode is a follow-up if
  real workloads ask for it.

### Neutral

- Picklability (ADR-0007) still applies to the multiprocessing
  strategy and is irrelevant to the async strategy.
- The `injector` container is process-local; the async strategy
  uses a single process, so no rehydration is needed for it.

## Alternatives considered

### Option A — Replace multiprocessing with asyncio framework-wide

- **Pro:** One execution model.
- **Con:** Pandas-in-event-loop is exactly the GIL anti-pattern
  ADR-0007 called out. Forces every existing user to rewrite.
- **Why rejected:** The CPU-bound case from ADR-0007 is still
  real; replacing the strategy would lose that audience.

### Option B — Async in a separate package (`pdip-async`)

- **Pro:** Strict isolation; users opt in via a different import
  path.
- **Con:** Duplicates the integrator scaffolding (factories,
  config loader, DI bootstrap) and forces version pinning between
  two packages.
- **Why rejected:** ADR-0014 established that *extras* are the
  unit of optionality in this project; following that pattern is
  cheaper than a sibling package.

### Option C — Threads instead of asyncio

- **Pro:** Already supported via `ParallelThreadIntegrationExecute`;
  no new dependency.
- **Con:** GIL caps throughput for any per-row Python work; thread
  pools do not solve the "thousands of in-flight I/O" case as
  cleanly as a single event loop.
- **Why rejected:** Threads stay as an option (they did not go
  anywhere), but they do not subsume the async use-case.

### Option D — Use Trio or AnyIO instead of native asyncio

- **Pro:** Cleaner cancellation semantics.
- **Con:** All the production-ready async DB drivers we depend on
  in §2 expose `asyncio` APIs; using AnyIO adds an abstraction
  layer for negligible benefit on our use case.
- **Why rejected:** Adopt asyncio directly; revisit if cancellation
  semantics become a real pain point.

## Follow-ups

- First-implementation PR: ship `AsyncConnectionSourceAdapter` /
  `AsyncConnectionTargetAdapter` base classes, the `pdip[async]`
  extra, and one async sibling end-to-end (Postgres source via
  `asyncpg` is the smallest tractable slice — single dependency,
  well-typed driver). Includes the new `async` strategy registered
  in the factory. TDD per ADR-0027: tests assert the factory
  raises a clear `ImportError` when the extra is absent and that
  the async strategy round-trips a small dataset against an
  asyncpg fixture.
- Subsequent PRs: one connector per PR (MySQL via aiomysql; MSSQL
  via aioodbc; Oracle via `oracledb` async; Kafka via aiokafka).
- README install table + `docs/async.md` page.
- Header note added to [ADR-0007](./0007-multiprocessing-for-etl.md)
  pointing to this ADR.
- Coordinate with [ADR-0033](./0033-opentelemetry-observability.md)
  so the async strategy emits the documented `pdip.integrator.step`
  span with `pdip.step.strategy = "async"` from the first PR.
- Coordinate with [ADR-0034](./0034-one-zero-readiness-criteria.md)
  so the new public symbols enter the 1.0 audit's `__all__`
  classification.

## References

- Code seams:
  `pdip/integrator/connection/base/connection_source_adapter.py`,
  `pdip/integrator/connection/base/connection_target_adapter.py`,
  `pdip/integrator/connection/factories/connection_source_adapter_factory.py`,
  `pdip/integrator/connection/factories/connection_target_adapter_factory.py`,
  `pdip/integrator/integration/types/sourcetotarget/strategies/factories/integration_execute_strategy_factory.py`,
  `pdip/integrator/integration/types/sourcetotarget/strategies/singleprocess/`,
  `pdip/integrator/integration/types/sourcetotarget/strategies/parallelthread/`,
  `pdip/integrator/integration/types/sourcetotarget/strategies/parallelold/`.
- [ADR-0007](./0007-multiprocessing-for-etl.md) — the decision this
  ADR partially supersedes.
- [ADR-0014](./0014-optional-extras-packaging.md) — extras pattern.
- [ADR-0021](./0021-cx-oracle-to-python-oracledb.md), [ADR-0022](./0022-kafka-python-replacement.md)
  — driver migrations that unlocked async siblings.
- [ADR-0027](./0027-tdd-with-diff-coverage.md) — TDD discipline.
- [ADR-0033](./0033-opentelemetry-observability.md), [ADR-0034](./0034-one-zero-readiness-criteria.md)
  — concurrent ADRs.
- External: [PEP 3156 (asyncio)](https://peps.python.org/pep-3156/),
  [asyncpg](https://magicstack.github.io/asyncpg/),
  [aiomysql](https://aiomysql.readthedocs.io/),
  [aioodbc](https://aioodbc.readthedocs.io/),
  [aiokafka](https://aiokafka.readthedocs.io/),
  [oracledb async](https://python-oracledb.readthedocs.io/en/latest/user_guide/asyncio.html).
