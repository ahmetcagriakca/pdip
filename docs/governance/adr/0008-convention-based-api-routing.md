# ADR-0008: Derive Flask-Restx routes by convention from controller modules

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** api, web

## Context

pdip's optional REST API is built on Flask-Restx. Flask-Restx expects
explicit namespace registration and explicit route declarations per
resource. In a framework that exposes dozens of endpoints, that
boilerplate adds up and the wiring becomes the single largest source of
merge conflicts when multiple features land in parallel.

We want new endpoints to appear by adding one file — the controller —
without touching a central registration module.

## Decision

Controller classes live in `pdip/api/` and derive from
`pdip/api/base/controller_base.py`. The framework's `Controller` helper:

- Derives the Flask-Restx namespace from the controller's **module path**.
- Discovers HTTP verb handlers on the class by the method name
  (`get`, `post`, `put`, `delete`) and registers them automatically.
- Uses Flask-Injector to wire constructor dependencies.

Request payloads are converted from HTTP into typed DTOs by
`pdip/api/converter/` and then dispatched via the CQRS dispatcher
(see [ADR-0003](./0003-cqrs-dispatcher.md)).

Errors are funnelled through a single `ErrorHandlers`
(`pdip/api/handlers/`) that understands `OperationalException`, generic
exceptions, and HTTP exceptions, and returns a consistent response
shape.

## Consequences

### Positive

- Adding an endpoint is a one-file change.
- The namespace layout mirrors the module layout, which is predictable
  for readers.
- Errors produce a consistent response shape because every request
  passes through the same handler chain.

### Negative

- Route URLs are derived from module paths. Renaming a module renames
  a public URL — a breaking change — so renames need care.
- Non-standard verbs (PATCH, OPTIONS) are not part of the convention
  and need a manual opt-in if ever required.
- Convention-based discovery is less explicit than a central router;
  a new contributor has to know the rule before they can find where
  a URL is defined.

### Neutral

- The `FlaskAppWrapper` (`pdip/api/app/flask_app_wrapper.py`) is an
  `ISingleton`. Tests that need a fresh app create a new wrapper inside
  a test-scoped container.

## Alternatives considered

### Option A — Explicit registration in a central `routes.py`

- **Pro:** Every route is visible in one place.
- **Con:** Every new feature edits the same file; becomes a merge
  hotspot.
- **Why rejected:** Convention scales better for a multi-contributor
  framework.

### Option B — FastAPI with decorators

- **Pro:** Type-driven validation, OpenAPI for free.
- **Con:** Requires asyncio throughout — conflicts with
  [ADR-0007](./0007-multiprocessing-for-etl.md)'s sync model — and
  replaces Flask, which is already widely understood.
- **Why rejected:** Not worth the churn given the current ecosystem.

### Option C — Bare Flask blueprints

- **Pro:** Minimal dependency surface.
- **Con:** Flask-Restx gives us namespace-based Swagger documentation
  and request validation for free.
- **Why rejected:** Swagger and validation are worth the extra
  dependency.

## Follow-ups

- Document the URL-derivation rules (module path → namespace) in the
  contributor guide; the rule is too easy to misremember without a
  written reference.

## References

- Code: `pdip/api/app/flask_app_wrapper.py`,
  `pdip/api/base/controller_base.py`,
  `pdip/api/handlers/`,
  `pdip/api/converter/`
