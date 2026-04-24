<p align="left">
    <a href="https://pypi.org/project/pdip" target="_blank">
        <img src="https://img.shields.io/pypi/v/pdip?color=%2334D058&label=pypi%20package" alt="Package version">
    </a>
    <a href="https://pypi.org/project/pdip" target="_blank">
        <img src="https://img.shields.io/pypi/pyversions/pdip.svg?color=%2334D058" alt="Supported Python versions">
    </a>
    <a href="https://github.com/ahmetcagriakca/pdip/blob/main/LICENSE" target="_blank">
        <img src="https://img.shields.io/github/license/ahmetcagriakca/pdip" alt="License">
    </a>
    <a href="https://github.com/ahmetcagriakca/pdip/actions/workflows/package-build-and-tests.yml" target="_blank">
        <img src="https://github.com/ahmetcagriakca/pdip/actions/workflows/package-build-and-tests.yml/badge.svg" alt="Build status">
    </a>
</p>

# pdip — Python Data Integrator

**pdip** is a batteries-included Python framework for building data
integration services. It bundles a dependency-injection container, a
CQRS dispatcher, a repository abstraction over SQLAlchemy, an
integration engine that moves data between SQL, big-data, web, file,
and in-memory backends, and an optional Flask-Restx API layer.

The goal is to let you write a new ETL job, CQRS use case, or REST
endpoint by adding one file — not by wiring plumbing.

## Contents

- [Why pdip?](#why-pdip)
- [Installation](#installation)
- [Quickstart — bootstrapping an app](#quickstart--bootstrapping-an-app)
- [Example — a CQRS handler](#example--a-cqrs-handler)
- [Example — a REST endpoint](#example--a-rest-endpoint)
- [Example — an ETL integration](#example--an-etl-integration)
- [Project layout](#project-layout)
- [Development](#development)
- [Documentation and governance](#documentation-and-governance)
- [License](#license)

## Why pdip?

- **Opinionated wiring.** Declare a service by inheriting from
  `ISingleton` or `IScoped` and it is auto-discovered and injected.
  No central registration file.
- **One language of use cases.** Commands and queries go through a
  single `Dispatcher`. Handlers are discovered by convention next to
  their request class.
- **Multi-backend integration.** A source→target adapter model that
  covers MSSQL, Oracle, PostgreSQL, MySQL, SQLite, Kafka, Impala,
  ClickHouse, CSV, Excel, SOAP, REST, and in-memory.
- **Tenant- and audit-aware by default.** Every entity carries audit
  columns and a tenant id; soft delete is the default.
- **Pay for what you use.** Heavy dependencies (pandas, DB drivers,
  Flask) are opt-in via `extras_require`.

The *why* behind each of these decisions is documented in the
[Architecture Decision Records](docs/governance/adr/README.md).

## Installation

pdip ships a slim core with optional feature sets:

```bash
# Core only (DI, CQRS, config, SQLAlchemy)
pip install pdip

# With the REST API layer
pip install "pdip[api]"

# With the ETL / integration engine and database drivers
pip install "pdip[integrator]"

# Everything
pip install "pdip[api,integrator,cryptography]"
```

Python **3.8+** is supported.

The extras are defined in [`setup.py`](setup.py). See
[ADR-0014](docs/governance/adr/0014-optional-extras-packaging.md) for
the rationale.

## Quickstart — bootstrapping an app

pdip boots through a single entry point, `Pdi`, which owns the
dependency injection container.

```python
# app.py
from pdip import Pdi
from pdip.logging.loggers.console import ConsoleLogger

pdi = Pdi()                          # auto-discovers services in this project

logger = pdi.get(ConsoleLogger)      # resolve any registered service
logger.info("pdip is ready")
```

Configuration is read from `application.yml` next to `app.py`, with
environment-specific overlays (`application.production.yml`) and
environment-variable overrides. See
[ADR-0005](docs/governance/adr/0005-yaml-configuration-with-env-overrides.md).

## Example — a CQRS handler

Place a command (or query) and its handler in the same module. The
dispatcher finds the handler by convention.

```python
# app/accounts/create_account.py
from pdip.cqrs import ICommand, ICommandHandler
from pdip.cqrs.decorators import dtoclass


@dtoclass
class CreateAccountCommand(ICommand):
    email: str
    display_name: str


class CreateAccountCommandHandler(ICommandHandler[CreateAccountCommand]):
    def handle(self, command: CreateAccountCommand):
        # validate, persist through a repository, publish events, ...
        return {"ok": True}
```

Dispatch from anywhere that can resolve the dispatcher:

```python
from pdip import Pdi
from pdip.cqrs import Dispatcher
from app.accounts.create_account import CreateAccountCommand

pdi = Pdi()
dispatcher = pdi.get(Dispatcher)
dispatcher.dispatch(CreateAccountCommand(email="a@b.com", display_name="Alice"))
```

See [ADR-0003](docs/governance/adr/0003-cqrs-dispatcher.md) for how
handler discovery works.

## Example — a REST endpoint

With the `[api]` extra installed, a Flask-Restx controller is one
file. The URL path is derived from the module path; `get`, `post`,
`put`, and `delete` methods are auto-registered.

```python
# app/api/accounts_controller.py
from injector import inject

from pdip.api.base import ControllerBase
from pdip.cqrs import Dispatcher

from app.accounts.create_account import CreateAccountCommand


class AccountsController(ControllerBase):
    @inject
    def __init__(self, dispatcher: Dispatcher):
        self.dispatcher = dispatcher

    def post(self, body):
        command = CreateAccountCommand(**body)
        return self.dispatcher.dispatch(command)
```

See [ADR-0008](docs/governance/adr/0008-convention-based-api-routing.md)
for the routing convention.

## Example — an ETL integration

With the `[integrator]` extra installed, `pdip.integrator` moves data
between a source and a target using adapters. The shape of an
integration is:

```
Operation
 └── Integration(s)
       ├── Source connection (SQL / BigData / WebService / File / InMemory)
       └── Target connection (SQL / BigData / WebService / File / InMemory)
```

A minimal invocation from application code:

```python
from pdip import Pdi
from pdip.integrator.base import Integrator

pdi = Pdi()
integrator = pdi.get(Integrator)

# `operation` is an OperationBase you build from your own models
# (see pdip/integrator/operation/domain/operation.py for the shape).
integrator.integrate(operation, execution_id="local-run-1")
```

The executor is process-based for throughput
([ADR-0007](docs/governance/adr/0007-multiprocessing-for-etl.md)) and
emits lifecycle events through a pub/sub broker
([ADR-0006](docs/governance/adr/0006-pubsub-message-broker.md)) so
observers can react without touching the pipeline.

## Project layout

```
pdip/
├── api/                REST API layer (Flask-Restx)
├── base/               Pdi entry point
├── configuration/      YAML + environment configuration
├── cqrs/               Command / query / dispatcher
├── cryptography/       Encryption helpers
├── data/               Repository, entity, session manager
├── delivery/           Email & notification providers
├── dependency/         DI container, service provider, scopes
├── exceptions/         Custom exception hierarchy
├── html/               HTML template service
├── integrator/         ETL engine, connections, pub/sub, initializers
├── io/                 File / stream utilities
├── json/               JSON helpers
├── logging/            Console logger
├── processing/         Multiprocessing primitives
└── utils/              Small helpers
```

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run the unit and integration test suite
python run_tests.py

# Run with coverage (same as CI)
coverage run --source=pdip run_tests.py
coverage report -m --omit="*/tests/*,*/site-packages/*"
```

Detailed test commands are in [`readme.test.md`](readme.test.md).
CI runs `package-build-and-tests.yml` on Python 3.9–3.11 across Linux,
macOS, and Windows.

## Documentation and governance

- [`docs/governance/`](docs/governance/README.md) — governance
  methodology, policies, and the ADR index that documents *why* pdip
  is built this way.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to contribute and the
  English-only content rule
  ([ADR-0016](docs/governance/adr/0016-english-only-content.md)).
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) — community norms.
- [`SECURITY.md`](SECURITY.md) — reporting vulnerabilities.
- [`CHANGELOG.md`](CHANGELOG.md) — release notes.

## License

Released under the [MIT License](LICENSE).
