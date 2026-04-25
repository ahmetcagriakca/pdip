# Public API surface

This page is the human-readable mirror of [ADR-0034](governance/adr/0034-one-zero-readiness-criteria.md)
§1. Every symbol below is part of the 1.0 contract: SemVer rules
apply, removals follow the deprecation policy in ADR-0034 §3, and a
machine-checked drift test
([`tests/unittests/public_api/test_public_api_contract.py`](../tests/unittests/public_api/test_public_api_contract.py))
fails CI when this table, the matching `__all__`, and the actual
package shape disagree.

If a symbol you expected to use is **not** listed here, it is
internal — it may move or change shape between any two 1.x releases
without warning. Open an issue if you need it promoted.

## Public packages

| Package | Public symbols | Source |
|---|---|---|
| `pdip` | *(empty — use submodules)* | [`pdip/__init__.py`](../pdip/__init__.py) |
| `pdip.api` | *(empty — Flask-Restx layer is composed by the host)* | [`pdip/api/__init__.py`](../pdip/api/__init__.py) |
| `pdip.configuration` | `ConfigManager` | [`pdip/configuration/__init__.py`](../pdip/configuration/__init__.py) |
| `pdip.cqrs` | `CommandQueryBase`, `CommandQueryHandlerBase`, `Dispatcher`, `ICommand`, `ICommandHandler`, `IQuery`, `IQueryHandler` | [`pdip/cqrs/__init__.py`](../pdip/cqrs/__init__.py) |
| `pdip.cryptography` | `CryptoService` | [`pdip/cryptography/__init__.py`](../pdip/cryptography/__init__.py) |
| `pdip.data` | *(empty — repository plumbing is composed by the host)* | [`pdip/data/__init__.py`](../pdip/data/__init__.py) |
| `pdip.delivery` | `EmailProvider` | [`pdip/delivery/__init__.py`](../pdip/delivery/__init__.py) |
| `pdip.dependency` | `IScoped`, `ISingleton` | [`pdip/dependency/__init__.py`](../pdip/dependency/__init__.py) |
| `pdip.exceptions` | `IncompatibleAdapterException`, `NotSupportedFeatureException`, `OperationalException`, `RequiredClassException` | [`pdip/exceptions/__init__.py`](../pdip/exceptions/__init__.py) |
| `pdip.html` | `HtmlTemplateService`, `Pagination` | [`pdip/html/__init__.py`](../pdip/html/__init__.py) |
| `pdip.integrator` | *(empty — entry points are composed via DI)* | [`pdip/integrator/__init__.py`](../pdip/integrator/__init__.py) |
| `pdip.io` | `FileManager`, `FolderManager` | [`pdip/io/__init__.py`](../pdip/io/__init__.py) |
| `pdip.json` | `BaseConverter`, `DateTimeEncoder`, `JsonConvert`, `MultipleJsonEncoders`, `UUIDEncoder`, `date_time_parser` | [`pdip/json/__init__.py`](../pdip/json/__init__.py) |
| `pdip.logging` | *(empty — concrete loggers are composed by the host)* | [`pdip/logging/__init__.py`](../pdip/logging/__init__.py) |
| `pdip.observability` | `get_meter`, `get_tracer` (lazy no-op-by-default OpenTelemetry helpers — install `pdip[observability]` and set `PDIP_OBSERVABILITY_ENABLED=1` to emit) | [`pdip/observability/__init__.py`](../pdip/observability/__init__.py) |
| `pdip.processing` | `ProcessManager` | [`pdip/processing/__init__.py`](../pdip/processing/__init__.py) |
| `pdip.utils` | `ModuleFinder`, `TypeChecker`, `Utils` | [`pdip/utils/__init__.py`](../pdip/utils/__init__.py) |

Empty rows are deliberate: they say "this namespace is reserved as
public, but nothing is currently re-exported from it." Adding a
symbol later is a non-breaking minor; switching the row from empty
to populated does not require a deprecation cycle.

## Adding or removing a public symbol

1. Edit `__all__` in the package's `__init__.py`.
2. Edit the row in the table above.
3. Edit the `EXPECTED_PUBLIC_SURFACE` mapping in
   [`tests/unittests/public_api/test_public_api_contract.py`](../tests/unittests/public_api/test_public_api_contract.py).
4. For removals only: emit a `DeprecationWarning` from the symbol
   for at least one full minor release before the removing PR — see
   [ADR-0034 §3](governance/adr/0034-one-zero-readiness-criteria.md).
5. Note the change under `[Unreleased]` in
   [`CHANGELOG.md`](../CHANGELOG.md).

The three artefacts (the `__all__`, this table, the test mapping)
must move together. The contract test fails CI if they disagree.
