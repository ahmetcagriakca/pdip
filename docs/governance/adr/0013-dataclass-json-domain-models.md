# ADR-0013: Model domain objects with `@dataclass_json` dataclasses

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** domain, serialization

## Context

pdip's integrator, CQRS, and API layers pass a steady stream of
structured data across internal boundaries:

- Controllers receive JSON and convert it to request DTOs.
- The CQRS dispatcher passes commands and queries to handlers.
- The integrator ships operation/execution records across process
  boundaries (see [ADR-0007](./0007-multiprocessing-for-etl.md)).
- The pub/sub broker carries `TaskMessage` events
  (see [ADR-0006](./0006-pubsub-message-broker.md)).

All of these need type-hinted fields, JSON round-trip support, and
picklability for the multiprocess boundary.

## Decision

Domain objects are modelled as Python dataclasses decorated with
`dataclasses_json.@dataclass_json`. pdip exposes three composable
decorators in `pdip/cqrs/decorators/`:

- `@dtoclass` — base combination (dataclass + JSON conversion).
- `@request_class` — marks a request DTO (typically the payload of a
  command or query).
- `@response_class` — marks a response DTO.

The integrator's operation and execution models live under
`pdip/integrator/**/domain/` and use the same decorators. The API
converters (`pdip/api/converter/`) rely on `@dataclass_json` to hydrate
DTOs from JSON and paging/order-by specifications from query strings.

## Consequences

### Positive

- One model class serves validation (through type hints), JSON
  serialization, and construction.
- No pydantic or marshmallow dependency; the dataclass is already part
  of the standard library.
- Dataclasses are picklable by default, which matters for the
  multiprocess executor.

### Negative

- `dataclasses_json` does not validate types at runtime. A caller that
  passes `"42"` where an `int` is expected sees the string travel all
  the way to the handler unless the code checks explicitly.
- Forward references and complex generics occasionally need manual
  `dataclasses_json` configuration.

### Neutral

- DTOs are mutable by default. Contributors who want immutability can
  pass `frozen=True` to the underlying dataclass.

## Alternatives considered

### Option A — pydantic

- **Pro:** Strict runtime validation, excellent error messages,
  OpenAPI-friendly.
- **Con:** Heavy dependency; v1 → v2 churn made upgrade costs high.
  pydantic models are not plain dataclasses, which complicates pickling
  and the dataclass-centric ecosystem we already have.
- **Why rejected:** Too much ecosystem disruption for the benefit we
  need.

### Option B — marshmallow schemas

- **Pro:** Mature, well-understood.
- **Con:** Two-class model (domain + schema) doubles the surface per
  DTO.
- **Why rejected:** Duplication outweighs the validation benefit.

### Option C — Plain dataclasses with hand-rolled JSON

- **Pro:** Zero dependencies.
- **Con:** Every new DTO re-invents `to_dict` / `from_dict`.
- **Why rejected:** `dataclasses_json` removes the boilerplate for a
  single-line dependency cost.

## Follow-ups

- When stricter validation is needed (untrusted API inputs in
  particular), add a thin validation layer in front of the DTO — keep
  the DTO itself simple.

## References

- Code: `pdip/cqrs/decorators/`,
  `pdip/integrator/operation/domain/operation.py`,
  `pdip/integrator/integration/domain/base/integration.py`,
  `pdip/api/converter/`
