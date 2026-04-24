# Architecture Decision Records

This is the index of ADRs for **pdip**. Each entry records a decision that
shapes how the framework is built and used. See the parent
[governance README](../README.md) for the methodology and lifecycle.

## Index

| # | Title | Status | Tags |
|---|---|---|---|
| [0001](./0001-dependency-injection-framework.md) | Adopt the `injector` library for dependency injection | Accepted | di, core |
| [0002](./0002-custom-di-scopes.md) | Expose custom DI scopes via `ISingleton` and `IScoped` | Accepted | di, lifecycle |
| [0003](./0003-cqrs-dispatcher.md) | Dispatch commands and queries through a single CQRS dispatcher | Accepted | cqrs, application |
| [0004](./0004-repository-pattern-sqlalchemy.md) | Expose data access through a generic repository over SQLAlchemy | Accepted | data, orm |
| [0005](./0005-yaml-configuration-with-env-overrides.md) | Load configuration from YAML with environment variable overrides | Accepted | configuration |
| [0006](./0006-pubsub-message-broker.md) | Use a pub/sub message broker for integration lifecycle events | Accepted | integrator, eventing |
| [0007](./0007-multiprocessing-for-etl.md) | Use `multiprocessing` (not `asyncio`) for ETL parallelism | Accepted | integrator, concurrency |
| [0008](./0008-convention-based-api-routing.md) | Derive Flask-Restx routes by convention from controller modules | Accepted | api, web |
| [0009](./0009-soft-delete-gcrecid.md) | Logically delete rows via `GcRecId` instead of physical `DELETE` | Accepted | data, retention |
| [0010](./0010-audit-columns-on-base-entity.md) | Put audit columns on the `Entity` base class | Accepted | data, audit |
| [0011](./0011-multi-tenancy-via-tenant-id.md) | Carry a `TenantId` on every entity for multi-tenant isolation | Accepted | data, multi-tenancy |
| [0012](./0012-connection-source-target-adapters.md) | Abstract sources and targets behind adapter interfaces | Accepted | integrator, connections |
| [0013](./0013-dataclass-json-domain-models.md) | Model domain objects with `@dataclass_json` dataclasses | Accepted | domain, serialization |
| [0014](./0014-optional-extras-packaging.md) | Ship optional dependencies as `extras_require` feature sets | Accepted | packaging, distribution |
| [0015](./0015-service-auto-discovery.md) | Auto-discover services by importing all modules at startup | Accepted | di, bootstrap |
| [0016](./0016-english-only-content.md) | Documentation, code, and commit messages are English-only | Accepted | documentation, contribution |

## Status legend

- **Accepted** — the decision is in force.
- **Deprecated** — still in the codebase but not recommended for new work.
- **Superseded by ADR-XXXX** — replaced by a newer ADR.

## Adding a new ADR

1. Copy [`template.md`](./template.md) to `NNNN-short-title.md`.
2. Fill in the sections.
3. Add a row to the index above.
4. Open a PR titled `ADR-NNNN: <short decision>`.

See the [governance README](../README.md) for the full lifecycle.
