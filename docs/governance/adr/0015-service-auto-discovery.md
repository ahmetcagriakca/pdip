# ADR-0015: Auto-discover services by importing all modules at startup

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** di, bootstrap

## Context

With the DI model in [ADR-0001](./0001-dependency-injection-framework.md)
and the scope markers in [ADR-0002](./0002-custom-di-scopes.md), every
service is declared at its class definition by inheriting from
`ISingleton` or `IScoped`. For the container to bind these at startup,
it has to know the classes exist. Python does not discover classes that
are never imported.

We do not want contributors to maintain a central registration file —
that becomes a merge conflict magnet and grows as the framework grows.

## Decision

At startup, the `ServiceProvider` walks the project's root directory
(inferred from the caller of `Pdi` in `pdip/base/pdi.py`) and imports
every Python module inside it, skipping a configurable
`excluded_modules` list. Once imports are done, `__subclasses__()` on
`ISingleton` and `IScoped` yields the full set of services to bind to
the container.

The same auto-discovery runs inside worker subprocesses
(see [ADR-0007](./0007-multiprocessing-for-etl.md)) so that workers
rehydrate with the same service graph as the parent process.

## Consequences

### Positive

- Registering a service is a one-line change: inherit from the marker.
  No central registry to edit.
- The service graph always reflects what is actually in the codebase.
- Workers converge to the same container state as the parent without
  shipping the container across the process boundary.

### Negative

- Startup imports the whole project. Import-time side effects will
  always fire. Contributors must keep modules import-safe.
- Diagnosing "why is this service not registered?" requires knowing
  that auto-discovery depends on import, which depends on the module
  being reachable from the root directory and not on the excluded
  list.
- Startup time grows linearly with codebase size. For most consumers
  this is milliseconds; for very large apps it becomes measurable.

### Neutral

- The excluded-modules list is the escape hatch. Modules with
  expensive or environment-sensitive imports (for example, a module
  that connects to a service at import time) can be excluded.

## Alternatives considered

### Option A — Central registration file

- **Pro:** Explicit; no import-time magic.
- **Con:** Every new service touches the registration file; merges
  conflict.
- **Why rejected:** Operational cost of maintaining the file outweighs
  the explicitness benefit.

### Option B — Decorator-based self-registration (`@service`)

- **Pro:** Marker and registration in one place; no subclass check.
- **Con:** Still needs imports to run; moves the marker from type
  hierarchy to decorator but keeps the import requirement.
- **Why rejected:** Not a substantive improvement over the marker-
  interface approach, and loses the benefit of `isinstance` checks.

### Option C — Package metadata entry points

- **Pro:** Standard Python packaging hook; works across installed
  packages.
- **Con:** Forces pdip consumers to package their services and declare
  entry points in `setup.py`, which is overkill for application code.
- **Why rejected:** Too heavy for application-level wiring.

## Follow-ups

- Consider caching the discovered subclass set per root directory to
  shave startup time when `Pdi` is constructed more than once in a
  process (for example, in test suites).
- Document the `excluded_modules` escape hatch prominently.

## References

- Code: `pdip/dependency/provider/service_provider.py`,
  `pdip/base/pdi.py`,
  `pdip/dependency/scopes.py`
