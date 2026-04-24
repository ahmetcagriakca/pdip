# ADR-0011: Carry a `TenantId` on every entity for multi-tenant isolation

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** data, multi-tenancy

## Context

pdip is frequently deployed as a single-process integration platform
that serves several business tenants at once (for example, multiple
customers sharing one ETL service). We need tenant isolation without
forcing operators to run a separate database per tenant.

The isolation model must be:

- Cheap to operate (one database, one schema, many tenants).
- Cheap to forget-proof (queries should not silently cross tenants).
- Compatible with the repository pattern
  ([ADR-0004](./0004-repository-pattern-sqlalchemy.md)).

## Decision

Every entity that inherits from `Entity`
(`pdip/data/domain/entity.py`) carries a `TenantId` column. The
`Repository[T]` fills it from the current execution context on write
and the finders apply a `TenantId` filter on read. Tenant is a
first-class part of row identity, not an application-level concern.

Single-tenant deployments still use the column: they run with a fixed
tenant id (for example a zero UUID), which keeps the schema and the
code paths identical across deployment shapes.

## Consequences

### Positive

- Adding a tenant is a configuration change, not a schema change.
- Forgetting the tenant filter in application code is not possible
  through the standard repository API.
- The same deployment handles one tenant or many with no branching.

### Negative

- Cross-tenant reporting has to bypass the default filter explicitly —
  an action that is deliberately awkward to discourage mistakes.
- Index design must include `TenantId` in most composite indexes to
  keep per-tenant query plans efficient.
- A bug that writes the wrong `TenantId` is hard to spot after the
  fact. The framework mitigates this by sourcing `TenantId` from the
  execution context rather than user input.

### Neutral

- Multi-tenant isolation at the database level (per-tenant schemas or
  per-tenant databases) remains possible but is outside the default
  model; users who need it can swap `DatabaseSessionManager`
  configurations per tenant.

## Alternatives considered

### Option A — Database-per-tenant

- **Pro:** Strongest possible isolation.
- **Con:** Operational cost scales with number of tenants; migrations
  run N times.
- **Why rejected:** Over-engineered for the common case.

### Option B — Schema-per-tenant

- **Pro:** Middle ground between database-per-tenant and row-level.
- **Con:** Dialect support for per-connection search paths varies;
  migrations still run N times.
- **Why rejected:** Row-level isolation is simpler and enough for
  pdip's target use cases.

### Option C — No tenant column; rely on application-level filtering

- **Pro:** Simplest schema.
- **Con:** One missed filter leaks data across tenants. Unacceptable.
- **Why rejected:** The cost of a single bug is too high.

## Follow-ups

- Publish index-design guidance once tenant cardinality grows (who
  expects hundreds vs. thousands vs. millions of tenants?).
- Provide a test helper that fails loudly if a handler issues a
  cross-tenant query by mistake.

## References

- Code: `pdip/data/domain/entity.py`,
  `pdip/data/repository/repository.py`
