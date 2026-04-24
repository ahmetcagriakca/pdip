# ADR-0012: Abstract sources and targets behind adapter interfaces

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** integrator, connections

## Context

pdip moves data between a wide matrix of backends: SQL databases
(MSSQL, Oracle, PostgreSQL, MySQL, SQLite), big-data systems (Impala,
ClickHouse, Kafka), web services (SOAP, REST), files (CSV, Excel), and
in-memory data. The set of backends is open — users will add their own.

If the executor speaks directly to backend libraries, two problems
follow. First, the executor becomes a god-object with a branch per
backend. Second, adding a new backend means editing core code.

## Decision

We model sources and targets as adapters behind two stable interfaces
in `pdip/integrator/connection/`:

- `ConnectionSourceAdapter` — `get_source_data_count()`,
  `get_iterator()`, `get_source_data_with_paging()`.
- `ConnectionTargetAdapter` — the write-side counterpart.

A factory resolves the concrete adapter from an
`IntegrationConnectionBase` (`pdip/integrator/integration/domain/base/integration.py`)
whose type field distinguishes SQL, BigData, WebService, File, Queue,
or InMemory connections. Authentication (`Basic`, `Kerberos`, `SSPI`)
is modelled in the connection domain, not in the adapter, so the same
adapter can accept different auth.

The executor only talks to the abstract adapter. Adding a new backend
is adding a new adapter plus a new branch in the factory; the executor
does not change.

## Consequences

### Positive

- The executor is backend-agnostic; its complexity does not grow with
  the number of supported backends.
- New backends are a local change.
- Adapters can be tested against mock connections without a real
  database.

### Negative

- The adapter interface is the narrowest useful contract. Backend-
  specific features (partitioning hints, bulk-copy APIs, specialised
  cursors) must either be folded into the interface — making it wider
  for everyone — or exposed through a backend-specific escape hatch.
- The `get_source_data_with_paging` contract assumes the source can
  page. Non-paging sources (streams, Kafka) must either buffer or
  implement paging artificially.

### Neutral

- Adapter instances are not `ISingleton`; they are created per run
  because they hold connection state tied to the execution.

## Alternatives considered

### Option A — A single "read rows / write rows" function per backend

- **Pro:** Minimal interface surface.
- **Con:** No place to hang pagination, counts, or streaming. Would
  force every caller to own its own batching.
- **Why rejected:** Too thin for the executor's needs.

### Option B — Use each library's native API directly in the executor

- **Pro:** Full expressive power.
- **Con:** Executor becomes the union of every backend's idiosyncrasies.
- **Why rejected:** Does not scale.

### Option C — A fully streaming-first interface (async iterators)

- **Pro:** Uniform backpressure.
- **Con:** Conflicts with [ADR-0007](./0007-multiprocessing-for-etl.md)'s
  sync process-based concurrency model.
- **Why rejected:** Not compatible with our execution model today.

## Follow-ups

- Document how to add a new adapter (interface, factory entry, domain
  type) once the contributor guide exists.
- Consider a capability system ("this adapter supports streaming",
  "this adapter supports paging") if backend-specific behaviour starts
  to leak.

## References

- Code: `pdip/integrator/connection/`,
  `pdip/integrator/integration/domain/base/integration.py`
