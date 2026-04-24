# ADR-0010: Put audit columns on the `Entity` base class

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** data, audit

## Context

Regulated integration workflows — finance, healthcare, public sector —
often require the ability to answer "who changed this row, and when?"
for every table. Adding audit columns on a table-by-table basis is
error-prone: some tables get them, others forget, and the ORM mapping
drifts over time.

We want audit to be a framework property, not a per-table discipline.

## Decision

The `Entity` base (`pdip/data/domain/entity.py`) declares the following
columns and every domain table inherits from it:

- `CreateUserId`, `CreateUserTime`
- `UpdateUserId`, `UpdateUserTime`
- `GcRecId` (soft delete — see [ADR-0009](./0009-soft-delete-gcrecid.md))
- `TenantId` (multi-tenant scope — see
  [ADR-0011](./0011-multi-tenancy-via-tenant-id.md))

The `Repository[T]` populates these columns from the current execution
context on `insert()` and `update()` so application code never has to
set them by hand.

## Consequences

### Positive

- Audit is enforced by the base class; contributors cannot forget it.
- Schema reviews become simple: if the table inherits `Entity`, it has
  audit.
- The columns have stable, documented names, which makes downstream
  reporting uniform.

### Negative

- Every table carries six extra columns even when only a handful are
  semantically meaningful for that table.
- The audit signal is only as good as the caller's identity. A process
  that writes as "system" still satisfies the schema but gives less
  information than a user context would.

### Neutral

- Timestamps are server-local. Cross-timezone deployments should
  standardise on UTC at the application layer.

## Alternatives considered

### Option A — Audit tables shadowing live tables

- **Pro:** Keeps the live schema lean; records every state, not just
  "last writer".
- **Con:** Doubles schema maintenance; every migration must mirror.
- **Why rejected:** Too heavy for the default; users who need full
  change history can layer it on top (triggers, CDC, event sourcing).

### Option B — Trigger-based audit in the database

- **Pro:** Works regardless of who writes.
- **Con:** Dialect-specific; each backend needs its own trigger code.
- **Why rejected:** Conflicts with pdip's multi-dialect goal
  (see [ADR-0004](./0004-repository-pattern-sqlalchemy.md)).

### Option C — Per-table opt-in audit mixin

- **Pro:** Tables that do not need audit stay lean.
- **Con:** Makes "does this table have audit?" a per-file question.
- **Why rejected:** Uniformity beats minor storage savings here.

## Follow-ups

- Document the expected identity format for `CreateUserId` /
  `UpdateUserId` (UUID, principal name, or opaque string) in the
  contributor guide.

## References

- Code: `pdip/data/domain/entity.py`,
  `pdip/data/repository/repository.py`
