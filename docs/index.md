# pdip

**pdip** is a Python framework for building data integration services.
It bundles:

- A dependency-injection container with custom scopes
  (`ISingleton`, `IScoped`).
- A CQRS dispatcher with convention-based handler discovery.
- A repository abstraction over SQLAlchemy with built-in audit,
  soft-delete, and multi-tenant behaviour.
- An ETL engine with source/target adapters for SQL, big-data, web,
  file, and in-memory backends.
- An optional Flask-Restx REST API layer.

For installation, a quickstart, and minimal code examples, start at
the [repository README](https://github.com/ahmetcagriakca/pdip#readme).

## How to read this site

- **Contributing → Setup** walks through getting a local development
  environment working.
- **Governance → Overview** explains how architectural decisions are
  captured, reviewed, and evolved.
- **Governance → Architecture Decision Records** lists every
  architecturally significant decision taken on pdip, with the context,
  trade-offs, and alternatives for each one.
- **Governance → Policies** derives day-to-day contribution rules from
  the ADRs.
- **Governance → Security audit** is a snapshot of the declared
  dependency surface and recommended follow-ups.

## Building this site

This site is scaffolded with [MkDocs](https://www.mkdocs.org/) and the
[Material](https://squidfunk.github.io/mkdocs-material/) theme. To
preview locally:

```bash
pip install mkdocs-material
mkdocs serve
```

The configuration lives in [`mkdocs.yml`](https://github.com/ahmetcagriakca/pdip/blob/main/mkdocs.yml)
at the repository root.
