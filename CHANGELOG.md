# Changelog

All notable changes to **pdip** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
for the public API surface described in
[ADR-0014](docs/governance/adr/0014-optional-extras-packaging.md).

> Historical entries are best-effort reconstructions from the git
> history. Detailed per-release notes start with the next tagged
> release.

## [Unreleased]

### Added

- Governance methodology under `docs/governance/` with 23 Architecture
  Decision Records documenting existing pdip decisions.
- ADR-0017 — Python support matrix is owned by `python_requires` and
  cannot be quietly narrowed by a dependency upgrade.
- ADR-0018 — Testing strategy: unit / integration pyramid, CI gating
  on test exit code, dependency expectations, priority order for
  closing coverage gaps.
- ADR-0019 — Python 3.14 adoption plan: staged, CI-gated matrix
  expansion with 3.14 as a non-blocking job until the ecosystem
  catches up.
- ADR-0020 — Raise `python_requires` floor from 3.8 to 3.9.
- ADR-0021 — Migrate the Oracle adapter from `cx_Oracle` to
  `python-oracledb`.
- ADR-0022 — Replace `kafka-python` with `confluent-kafka` for the
  Kafka adapter.
- ADR-0023 — Coverage floor policy (`.coveragerc` with
  `fail_under=20` starting point and a ratchet plan).
- `.coveragerc` at the repo root, shared between local runs and CI.
- 17 new unit tests across Repository (9), ConfigManager env
  override (2), and `@dtoclass` decorator (6). Suite total goes
  from 48 to 65.
- `CHANGELOG.md` in Keep-a-Changelog format.
- Expanded `README.md` with installation matrix, quickstart, CQRS /
  REST / ETL examples, project layout, and governance links.
- `CONTRIBUTING.md` now links to the governance docs and surfaces the
  English-only content rule (ADR-0016).
- Dependency security audit at
  `docs/governance/security-audit-2026-04-24.md`.
- MkDocs-material scaffolding (`mkdocs.yml`, `docs/index.md`) that
  surfaces the governance docs.
- CI emits `coverage.xml` and `htmlcov/` as per-job artifacts.

### Changed

- **Python 3.14 is now a blocking CI job** across Linux, macOS, and
  Windows. The `continue-on-error: true` escape hatch from ADR-0019
  is dropped now that the suite is green on 3.14. Two pinned
  dependencies lacked 3.14 wheels and were bumped to the smallest
  patch release that does: `coverage` 7.6.10 → 7.6.12 and
  `PyYAML` 6.0.2 → 6.0.3.
- `requirements.txt` slimmed: `pandas`, `kafka-python`, and
  `func-timeout` moved out of the core install and now live only in
  the `integrator` extra where they belong (they are only imported by
  integration adapters). A clean `pip install -r requirements.txt`
  no longer needs to build pandas on Python versions without
  prebuilt wheels — the immediate cause of the previous 3.14 Linux
  and 3.14 macOS failures.
- `pdip.processing.ProcessManager` and
  `pdip.integrator.pubsub.MessageBroker` now pin the
  `multiprocessing` start method to **`spawn`** via
  `multiprocessing.get_context('spawn')`. Python 3.14 changed the
  default on POSIX from `fork` to `forkserver`; pinning `spawn`
  makes pdip's behaviour identical on Linux, macOS, and Windows
  across every supported Python.
- `pdip.utils.ModuleFinder.import_modules` strips leading dots
  before calling `importlib.import_module`. Python 3.14 now rejects
  a dotted name whose prefix is empty (a "relative import without
  package"); pdip produced such a name when the computed
  `module_base_address` was empty. Imports on 3.14 would crash the
  DI bootstrap before a single service was registered.
- `EndpointWrapper.get_annotations`, `RequestConverter.get_annotations`,
  and `BaseConverter.get_annotations` now resolve `__annotations__`
  from the **class**, not the instance. Python 3.14 no longer exposes
  `__annotations__` through instance attribute lookup, so the old
  code silently returned `None` on 3.14 — which meant the Flask-RESTx
  request parser had zero fields and every GET ignored its query
  string. Surfaced by `test_basic_app_with_cqrs`.
- Bumped safe patch-level dependencies picked up from open Dependabot
  PRs: `coverage` 7.5.1 → 7.6.10, `cryptography` 43.0.0 → 43.0.1,
  `pandas` 2.2.2 → 2.2.3, `PyYAML` 6.0.1 → 6.0.2, `Werkzeug` 3.0.3
  → 3.0.6.
- Bumped `injector` 0.21.0 → 0.22.0. Changelog for 0.22 adds PEP 593
  `Annotated` support and drops Python 3.7 (not in our supported
  window, so no effect).
- `mysql-connector-python` stays pinned at `8.4.0`. Dependabot's 9.1.0
  bump (PR #37) drops Python 3.8 support, which ADR-0017 forbids.
- CI matrix widened from `3.9/3.10/3.11` to `3.9/3.10/3.11/3.12/3.13`
  blocking, plus `3.14` non-blocking (`continue-on-error: true`). See
  ADR-0019 for the staging plan.
- CI upgraded `actions/checkout@v2 -> v4` and
  `actions/setup-python@v2 -> v5` with `allow-prereleases: true` so
  Python 3.14 installs cleanly.
- `setup.py` classifiers add `Python :: 3.12`, `3.13`, `3.14`.
- Added 24 new unit tests covering CQRS dispatcher, `Pdi` entry,
  pub/sub channel queue + publisher + `TaskMessage`, and json
  helpers. Suite went from 24 runs to 48.

### Fixed

- `tests/unittests/processing/test_process_manager.py::test_process_error`
  referenced `results[0]` instead of the loop variable, so the
  assertion passed only when the first subprocess happened to be
  the one that errored. Under `spawn` (the new default; see above)
  only one subprocess typically reports `State=4`, and when that
  was not index 0 the assertion failed. Rewritten to iterate the
  errored results.
- `pdip.data.repository.Repository.delete` / `delete_by_id` used
  `uuid.uuid4()` directly, producing a UUID object rather than the
  dialect-aware string the rest of the repository uses. On SQLite
  and other dialects without native UUID binding this raised
  `ProgrammingError: type 'UUID' is not supported`. The delete
  helpers now branch on dialect the same way `insert` and `update`
  do. Surfaced by the new `tests/unittests/data/test_repository.py`.
- `run_tests.py` now exits non-zero when any test errors or fails.
  Previously the guard was commented out and CI always reported
  green regardless of the result. See ADR-0018.
- `run_tests.py` test-case discovery now loads **every**
  `TestCase` subclass in a test module. The previous loop picked only
  one class per file so any file with multiple `TestCase` groupings
  silently dropped the others. After the fix, running the suite on
  Python 3.11 reports 48 tests instead of 24.
- `dataclasses-json` added to `requirements.txt`. Tests imported it
  indirectly through the integrator extras; a clean
  `pip install -r requirements.txt` failed to install it, which
  broke local runs for contributors and silently hid failures in
  CI (because of the exit-code bug above).

### Removed

- **Python 3.8 support.** `python_requires` raised from `>=3.8` to
  `>=3.9`, `Programming Language :: Python :: 3.8` classifier
  dropped. Rationale in ADR-0020: Python 3.8 reached end-of-life on
  2024-10-07, was never in the CI matrix, and was blocking
  `mysql-connector-python` 9.x. **Breaking** — consumers on 3.8 must
  upgrade their runtime or stay on pdip `0.6.x`.
- `dataclasses==0.6` — Python 3.6 backport; no-op on the supported
  matrix (`python_requires >= 3.9`).
- `Fernet==1.0.1` — third-party wrapper. pdip imports `Fernet` from
  the `cryptography` package (`cryptography.fernet.Fernet`), which
  was already the intended path.
- `Flask-Ext==0.1` — not imported anywhere in the codebase.

### Fixed

- `setup.py` references `README.md`; the file on disk was `readme.md`,
  which broke source distributions on case-sensitive filesystems. The
  file is now `README.md`.

## [0.6.10] — previously released

Baseline version at the time this changelog was introduced. Dependency
upgrades to this point include:

- `SQLAlchemy` bumped to `2.0.35`.
- `Flask-Cors` bumped to `5.0.0`.
- `cryptography` bumped to `43.0.0`.
- `dataclasses-json` bumped to `0.6.7`.
- `Werkzeug` bumped to `3.0.3`.

Earlier history is preserved in the git log; see
`git log --oneline` and the tags on the `ahmetcagriakca/pdip`
repository.

[Unreleased]: https://github.com/ahmetcagriakca/pdip/compare/v0.6.10...HEAD
[0.6.10]: https://github.com/ahmetcagriakca/pdip/releases/tag/v0.6.10
