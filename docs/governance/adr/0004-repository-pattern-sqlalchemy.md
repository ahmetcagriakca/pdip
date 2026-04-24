# ADR-0004: Expose data access through a generic repository over SQLAlchemy

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** data, orm

## Context

pdip reads and writes to multiple relational backends (MSSQL, Oracle,
PostgreSQL, MySQL, SQLite). Application code should not have to know
which dialect is in use, and handlers should not have to hand-craft
SQLAlchemy sessions, transactions, or audit-column bookkeeping on every
call.

We need a data-access layer that:

- Hides session and transaction plumbing from application code.
- Applies audit columns and multi-tenancy consistently (see
  [ADR-0010](./0010-audit-columns-on-base-entity.md) and
  [ADR-0011](./0011-multi-tenancy-via-tenant-id.md)).
- Preserves SQLAlchemy's power when a query cannot be expressed through
  the repository's finder helpers.

## Decision

We define a generic `Repository[T]` in `pdip/data/repository/repository.py`
parameterised by an entity type. Each repository takes an injected
`DatabaseSessionManager` (`pdip/data/base/database_session_manager.py`)
and exposes a small, stable API:

- Read: `get()`, `get_by_id()`, `first()`, `filter_by()`.
- Write: `insert()`, `update()`, `delete()` (soft delete — see
  [ADR-0009](./0009-soft-delete-gcrecid.md)), `commit()`.

Write operations populate audit fields (`CreateUserId`, `CreateUserTime`,
`UpdateUserId`, `UpdateUserTime`, `TenantId`) from the current execution
context so handlers never set them by hand.

Transactional boundaries are applied via the `@transactionhandler`
decorator in `pdip/data/decorators/`, which wraps a method with
commit-on-success / rollback-on-exception behaviour resolved through the
dependency container.

When a use case needs something the repository does not expose
(aggregates, joins, window functions), handlers may drop down to the
SQLAlchemy session directly via `DatabaseSessionManager` rather than
stretching the repository API.

## Consequences

### Positive

- Common CRUD is one line from handler code.
- Audit, soft-delete, and tenant logic are applied uniformly; a handler
  cannot forget them.
- Swapping RDBMS only requires a new dialect configuration (see
  [ADR-0005](./0005-yaml-configuration-with-env-overrides.md)), not a
  code change.

### Negative

- A generic repository cannot express every query. Contributors must
  know when to step past it and use the raw session.
- The repository API is small and intentionally CRUD-shaped; analytical
  workloads will not fit.

### Neutral

- Tests that use the repository need a `DatabaseSessionManager` fake or
  an in-memory SQLite session. A lightweight fixture covers both.

## Alternatives considered

### Option A — Handlers use SQLAlchemy sessions directly

- **Pro:** Full expressive power at every call site.
- **Con:** Audit columns, soft delete, and tenant scoping would be
  copy-pasted and easy to forget.
- **Why rejected:** Consistency of audit and tenant behaviour is more
  valuable than raw expressiveness at every call site.

### Option B — A query-builder DSL specific to pdip

- **Pro:** Could enforce tenant and soft-delete filtering at the type
  level.
- **Con:** Huge maintenance burden; re-invents SQLAlchemy.
- **Why rejected:** SQLAlchemy already does this better than we could.

### Option C — A different ORM (Django ORM, Peewee, Tortoise)

- **Pro:** Django's migration story is mature.
- **Con:** SQLAlchemy has the broadest dialect support and the deepest
  hook surface for our audit/soft-delete/tenant model.
- **Why rejected:** Dialect breadth is a hard requirement for an
  integration framework.

## Follow-ups

- Document the "when to bypass the repository" rule in the contributor
  guide once it exists.

## References

- Code: `pdip/data/repository/repository.py`,
  `pdip/data/base/database_session_manager.py`,
  `pdip/data/decorators/`
