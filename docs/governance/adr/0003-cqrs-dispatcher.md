# ADR-0003: Dispatch commands and queries through a single CQRS dispatcher

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** cqrs, application

## Context

pdip's API layer is expected to host a growing number of use cases. If
controllers call application services directly, each controller ends up
knowing which service and method to invoke and what DTOs to pass. Over
time this couples the transport layer (Flask routes) to the application
layer (business logic) and makes cross-cutting concerns (validation,
logging, transactions, auditing) hard to apply uniformly.

We want:

- A clear boundary between "intent to change state" (commands) and
  "intent to read state" (queries).
- A single seam where cross-cutting behaviour can be added later without
  editing every call site.
- A convention that scales to dozens of handlers without a large
  registration table.

## Decision

We implement a CQRS dispatcher in `pdip/cqrs/`:

- `ICommand` and `IQuery` are abstract markers for request objects.
- `CommandQueryBase[T]`, `ICommandHandler[CH]`, and `IQueryHandler[QH]`
  are generic bases parameterised by the request type.
- `Dispatcher` (registered as `IScoped`) is the single entry point.
  Controllers and application code call `dispatcher.dispatch(cmd_or_query)`.

Handler discovery is **by convention**: for a command or query defined
in module `foo.bar.Baz`, the dispatcher resolves a handler in the same
module named `BazHandler`. This removes the need for a central
registration table.

Request and response DTOs are marked with the decorators in
`pdip/cqrs/decorators/` — `@dtoclass`, `@request_class`, `@response_class` —
which compose `@dataclass` with JSON conversion (see
[ADR-0013](./0013-dataclass-json-domain-models.md)).

## Consequences

### Positive

- Controllers become thin: build a DTO, hand it to the dispatcher, shape
  the response.
- New cross-cutting concerns (logging, validation, transaction wrapping)
  can later be added inside `Dispatcher.dispatch` without editing
  handlers.
- The convention "handler lives next to its command" keeps related code
  together and is easy to navigate.

### Negative

- Reflection-based handler lookup is a small runtime cost and makes
  static tools (IDE "go to handler") work less well than explicit
  registration would.
- The dispatch convention is a *soft* contract: a misplaced handler is
  not caught at import time, only at dispatch time.
- We enforce a CQRS shape even for use cases that could have been a
  plain function call. That is a deliberate uniformity trade-off.

### Neutral

- Commands and queries travel through the same dispatcher, so the
  "separation" is semantic rather than physical. We accept this; a
  second dispatcher would add ceremony without adding value.

## Alternatives considered

### Option A — Controllers call application services directly

- **Pro:** Simplest possible wiring.
- **Con:** No single seam for cross-cutting behaviour; couples the web
  layer to service method signatures.
- **Why rejected:** Does not scale to the number of endpoints we expect.

### Option B — Explicit handler registration

- **Pro:** Static, introspectable, IDE-friendly.
- **Con:** Every new handler requires two edits (handler file + registry).
- **Why rejected:** Convention is cheaper and, given pdip's module
  layout, unambiguous.

### Option C — Event sourcing + full CQRS with separate read model

- **Pro:** Powerful for audit and scaling.
- **Con:** Massive complexity for a framework whose users may just want
  a REST CRUD.
- **Why rejected:** Far beyond the needs of pdip's consumers.

## Follow-ups

- If cross-cutting concerns proliferate, wrap `Dispatcher.dispatch` with
  a pipeline/behaviour chain rather than scattering decorators across
  handlers.

## References

- Code: `pdip/cqrs/dispatcher.py`, `pdip/cqrs/icommand.py`,
  `pdip/cqrs/iquery.py`, `pdip/cqrs/decorators/`
