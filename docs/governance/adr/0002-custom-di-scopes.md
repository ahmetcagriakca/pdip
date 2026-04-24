# ADR-0002: Expose custom DI scopes via `ISingleton` and `IScoped`

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** di, lifecycle

## Context

[ADR-0001](./0001-dependency-injection-framework.md) decided to use the
`injector` library as our container. `injector` ships two built-in
scopes — `singleton` and `noscope` — but pdip needs more than that:

- Configuration objects, logging, and the Flask wrapper must be
  process-wide singletons.
- Per-request services (CQRS dispatcher, repository instances,
  integration execution context) must be isolated across concurrent
  requests and across worker threads so that a SQLAlchemy session is not
  shared between requests.
- Contributors should not have to reason about `injector`'s scope API
  every time they register a service. They should pick one of a small
  number of well-documented lifetimes.

## Decision

We define three marker interfaces in `pdip/dependency/scopes.py` and use
them as the canonical way to declare an object's lifetime:

| Marker | Lifetime | Typical use |
|---|---|---|
| `IDependency` | Base marker. Not bound to a scope on its own. | Type unions in signatures. |
| `ISingleton` | One instance per process. | Config, logger, Flask wrapper, message broker. |
| `IScoped` | One instance per thread (thread-local). | Repositories, CQRS dispatcher, integration execution. |

At bootstrap (`ServiceProvider`), pdip walks every subclass of
`ISingleton` and `IScoped` and registers it with the corresponding
`injector` scope (`SingletonScope` and a thread-local scope). Contributors
do not call `injector.binder.bind(...)` directly.

## Consequences

### Positive

- A contributor only has to answer one question to register a new
  service: "is this shared across the process, or isolated per worker
  thread?"
- The scope decision is visible at the class declaration, not hidden in
  a separate wiring module.
- Thread-local scoping keeps SQLAlchemy sessions correctly isolated when
  Flask handles concurrent requests.

### Negative

- There is no out-of-the-box "transient" scope (a fresh instance on every
  resolution). In the rare case this is needed, callers construct the
  object themselves.
- Scope selection is encoded in the type hierarchy. Changing a service's
  lifetime is a source-level change, not a configuration change.

### Neutral

- Because `ISingleton` and `IScoped` are marker interfaces, they do not
  enforce method contracts. They are purely lifetime declarations.

## Alternatives considered

### Option A — Use `injector`'s scopes directly

- **Pro:** No custom abstractions.
- **Con:** Every registration needs bespoke `@singleton` or `scope=...`
  wiring; the auto-discovery in ADR-0015 would not work.
- **Why rejected:** Forces ceremony at every registration site.

### Option B — A single "request" scope tied to Flask

- **Pro:** Matches Flask's native request lifetime.
- **Con:** The integrator runs outside Flask (in worker subprocesses)
  and still needs per-execution isolation.
- **Why rejected:** Thread-local generalises cleanly to both the
  Flask and the worker-process cases.

## Follow-ups

- If a future use case demands a transient or request-scoped lifetime,
  add a new marker (e.g. `ITransient`) rather than overloading the
  existing ones.

## References

- Code: `pdip/dependency/scopes.py`,
  `pdip/dependency/provider/service_provider.py`
