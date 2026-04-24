# ADR-0001: Adopt the `injector` library for dependency injection

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** di, core

## Context

pdip is a framework that stitches together many moving parts: a REST API,
a data access layer, an integration engine, a multiprocess executor, a
logger, a cryptography service, an email delivery service, and so on. Most
of these subsystems depend on each other.

We need a way to wire these dependencies that:

- Keeps construction out of business logic so tests can replace collaborators.
- Works both inside a long-lived Flask process and inside short-lived
  worker subprocesses spawned by the integrator.
- Supports different object lifetimes (one per process vs. one per
  thread / request).
- Does not force every consumer of pdip to learn a heavy inversion-of-control
  framework.

Writing our own container is possible but it is a well-understood problem
and an existing library removes a surface we would otherwise have to
maintain and document.

## Decision

We use the third-party [`injector`](https://pypi.org/project/injector/)
library as pdip's dependency injection container.

Concrete wiring lives in `pdip/dependency/`:

- `provider/service_provider.py` wraps `injector.Injector` and exposes
  `get()`, scope-aware binding, and Flask integration.
- `container/dependency_container.py` provides a static facade so that
  code in worker processes (where we cannot pass the injector through the
  call stack) can still resolve services.
- `scopes.py` defines the marker interfaces (`IDependency`, `ISingleton`,
  `IScoped`) that drive scope selection — see [ADR-0002](./0002-custom-di-scopes.md).

The public entry point `pdip.Pdi` (`pdip/base/pdi.py`) hides the container
behind `Pdi.get(Type)` so that simple consumers never need to import
`injector` directly.

## Consequences

### Positive

- Business code declares collaborators via constructor `@inject`-style
  signatures and is trivially testable with fakes.
- We inherit `injector`'s scope machinery instead of building our own.
- Flask, Flask-Restx, and Flask-Injector already interoperate with
  `injector`, so the web layer wires up cleanly.

### Negative

- pdip is coupled to the `injector` library's API and release cadence.
  A breaking change upstream would ripple through the service provider.
- The static `DependencyContainer` facade is effectively a service locator
  and can hide dependencies if misused. We tolerate this because it is the
  only sane way to rehydrate the container inside a forked worker process.

### Neutral

- Contributors must learn the difference between `ISingleton` and
  `IScoped`. This is documented in ADR-0002.

## Alternatives considered

### Option A — Hand-rolled container

- **Pro:** No third-party dependency; tailor-fit to our needs.
- **Con:** Scope semantics, thread-local management, and Flask
  integration would all be ours to maintain.
- **Why rejected:** The cost of owning the container is higher than the
  cost of depending on `injector`.

### Option B — `dependency-injector` (the other PyPI library)

- **Pro:** Very feature-rich, supports providers, resources, wiring,
  async, and declarative configuration.
- **Con:** Heavier conceptual footprint; its "Provider" model is
  orthogonal to the simple class-as-binding model we prefer.
- **Why rejected:** More surface area than we need.

### Option C — No DI, pass dependencies manually

- **Pro:** Zero framework overhead.
- **Con:** Every subsystem would either import collaborators directly
  (tight coupling) or accept them through long constructor chains.
- **Why rejected:** Does not scale to the number of cross-cutting
  services pdip exposes.

## Follow-ups

- Keep `DependencyContainer` usage confined to bootstrap code and worker
  re-initialisation. New application code should prefer constructor
  injection.

## References

- Code: `pdip/dependency/provider/service_provider.py`,
  `pdip/dependency/container/dependency_container.py`,
  `pdip/base/pdi.py`
- External: <https://pypi.org/project/injector/>
