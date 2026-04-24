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

- Governance methodology under `docs/governance/` with 17 Architecture
  Decision Records documenting existing pdip decisions.
- ADR-0017 — Python support matrix is owned by `python_requires` and
  cannot be quietly narrowed by a dependency upgrade.
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

- Bumped safe patch-level dependencies picked up from open Dependabot
  PRs: `coverage` 7.5.1 → 7.6.10, `cryptography` 43.0.0 → 43.0.1,
  `pandas` 2.2.2 → 2.2.3, `PyYAML` 6.0.1 → 6.0.2, `Werkzeug` 3.0.3
  → 3.0.6.
- Bumped `injector` 0.21.0 → 0.22.0. Changelog for 0.22 adds PEP 593
  `Annotated` support and drops Python 3.7 (not in our supported
  window, so no effect).
- `mysql-connector-python` stays pinned at `8.4.0`. Dependabot's 9.1.0
  bump (PR #37) drops Python 3.8 support, which ADR-0017 forbids.

### Removed

- `dataclasses==0.6` — Python 3.6 backport; no-op on the supported
  matrix (`python_requires >= 3.8`).
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
