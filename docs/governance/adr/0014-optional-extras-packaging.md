# ADR-0014: Ship optional dependencies as `extras_require` feature sets

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** packaging, distribution

## Context

pdip is a framework that can be used for very different purposes:

- Someone writing a small CQRS service needs CQRS and DI but no Flask,
  no pandas, no database drivers.
- Someone writing an ETL batch needs pandas, pyodbc/cx_Oracle/etc.,
  and the integrator but no Flask REST API.
- Someone building a web service needs Flask, Flask-Restx, and
  Flask-Injector but maybe no database drivers.

If the core `pdip` package depends on everything, a small service pays
for pandas, pyodbc, cx_Oracle, kafka-python, and cryptography whether
it uses them or not. Those drivers also bring native build-time
dependencies (Oracle client, ODBC, etc.) that make installation
fragile.

## Decision

The core `pdip` package keeps its required dependency list short
(injector, SQLAlchemy, PyYAML, dataclasses-json). Optional capabilities
are exposed via `extras_require` feature sets in `setup.py`:

- `pdip[api]` — Flask, Flask-Restx, Flask-Injector, Flask-Cors.
- `pdip[integrator]` — pandas, driver packages, Kafka, func-timeout.
- `pdip[cryptography]` — cryptography/Fernet.

Consumers install the combination they need: `pip install pdip[api]`,
`pip install pdip[integrator,cryptography]`, and so on. Framework code
that depends on an extra imports its modules lazily so that installing
the core package without an extra does not crash at import time.

## Consequences

### Positive

- Small consumers stay small. CQRS-only services do not drag in
  pandas.
- Native-build drivers are only a concern for users who opt in.
- Upgrade paths are independent: a breaking pandas change only affects
  `integrator` users.

### Negative

- Contributors must remember to gate imports behind `try/except
  ImportError` (or lazy imports) when adding code that depends on an
  extra.
- The feature matrix has to be kept in sync between `setup.py`, the
  README install table, and our CI matrix.
- Users who install the wrong extra get `ImportError` at runtime
  rather than at install time.

### Neutral

- The extras names are part of our public interface; renaming them is
  a breaking change for consumers.

## Alternatives considered

### Option A — One mega-package with every dependency

- **Pro:** Simplest `pip install pdip`.
- **Con:** Pulls heavyweight native drivers for every install.
- **Why rejected:** Install friction is unacceptable for small
  services.

### Option B — One package per feature (pdip-api, pdip-integrator, ...)

- **Pro:** Fully independent versioning.
- **Con:** Dramatically increases release overhead for a small team;
  cross-package version pinning becomes the user's problem.
- **Why rejected:** Extras give most of the benefit at a fraction of
  the cost.

### Option C — Plugin architecture

- **Pro:** Ultimate extensibility; third-party backends become
  first-class.
- **Con:** Large design effort; not needed for the current user base.
- **Why rejected:** Premature.

## Follow-ups

- Document the full extras matrix in the README once user-facing docs
  are refreshed.
- Add a CI job per extras combination so that each installs cleanly on
  the supported Python versions.

## References

- Code: `setup.py`, `requirements.txt`
