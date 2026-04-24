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

- Governance methodology under `docs/governance/` with 16 Architecture
  Decision Records documenting existing pdip decisions.
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
  → 3.0.6. Major bumps (`injector` 0.22, `mysql-connector-python`
  9.x) remain open on their respective Dependabot PRs pending manual
  verification.

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
