# ADR-0009: Logically delete rows via `GcRecId` instead of physical `DELETE`

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** data, retention

## Context

pdip is used to build integration platforms. Users of those platforms
expect to be able to answer "what was the state of this record a week
ago?" and "who deleted this row and when?" for audit, debugging, and
regulatory reasons. A physical `DELETE` discards that history.

At the same time, indexes and foreign keys still need to behave
predictably, and "live" queries must not see deleted rows without the
application having to remember a filter every time.

## Decision

The `Entity` base (`pdip/data/domain/entity.py`) carries a `GcRecId`
("garbage collection record id") column. The `Repository[T]`
(`pdip/data/repository/repository.py`) treats `delete()` as a soft
delete: it sets `GcRecId` and audit fields (`UpdateUserId`,
`UpdateUserTime`) rather than issuing SQL `DELETE`. The default finders
(`get`, `first`, `filter_by`) exclude rows with a non-null `GcRecId` so
application code does not have to remember to filter.

Physical deletion is not exposed through the repository. Operators who
need to reclaim space run a purge job outside the application — an
explicit, auditable action.

## Consequences

### Positive

- Deletions are recoverable and traceable.
- Joins do not break because foreign keys still resolve to the row.
- Application code cannot accidentally lose data through the standard
  API.

### Negative

- Tables grow over time; indexes must accommodate the full set of rows.
  Purging is an operational concern.
- Unique constraints need to take `GcRecId` into account, either by
  adding `GcRecId` to the unique index or by enforcing uniqueness at
  the application layer.
- A consumer that queries the database directly (outside the
  repository) must remember the `GcRecId` filter themselves.

### Neutral

- "Undelete" is a matter of nulling `GcRecId` again. The repository does
  not expose this as a first-class operation; it is deliberately a
  manual action.

## Alternatives considered

### Option A — Physical delete

- **Pro:** Simple; storage stays flat.
- **Con:** Loses history; makes audit impossible.
- **Why rejected:** Conflicts with the framework's audit posture
  (see [ADR-0010](./0010-audit-columns-on-base-entity.md)).

### Option B — Move deleted rows to a shadow table

- **Pro:** Keeps the live table lean.
- **Con:** Doubles the schema; joins to history become awkward.
- **Why rejected:** Not worth the complexity at this scale.

### Option C — Event-sourced history

- **Pro:** Perfect audit by construction.
- **Con:** Requires a fundamentally different data model.
- **Why rejected:** Far beyond what pdip aims to be.

## Follow-ups

- Provide guidance (in the contributor guide, once it exists) on how to
  build unique indexes that cope with soft-deleted rows.
- Consider shipping a generic purge helper that takes a retention
  window.

## References

- Code: `pdip/data/domain/entity.py`,
  `pdip/data/repository/repository.py`
