# ADR-0024: Release process — semver, CHANGELOG, and PyPI publish

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** release, packaging, process

## Context

pdip is published on PyPI as [`pdip`](https://pypi.org/project/pdip).
Today the release process is implicit:

- `setup.py` reads the version from a `PYPI_PACKAGE_VERSION`
  environment variable, defaulting to `0.6.10`.
- [`.github/workflows/python-upload-package.yml`](../../../.github/workflows/python-upload-package.yml)
  and [`python-upload-test-package.yml`](../../../.github/workflows/python-upload-test-package.yml)
  build and upload on push, but neither the tagging scheme nor the
  mapping between code changes and version bumps is written down.
- `CHANGELOG.md` has an **Unreleased** section but no policy on when
  entries move into a numbered release.

The last ~half year of work in this repository (ADR-0017 through
ADR-0023) changed the public surface in meaningful ways — driver
swaps, the Python floor raise, the CI matrix. A release that does
not distinguish a patch fix from a Python-floor change is a trap
for every downstream consumer.

## Decision

### 1. Semantic versioning maps to CHANGELOG categories

pdip follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).
The `CHANGELOG.md` (Keep a Changelog format) is the canonical source
for what kind of release a given set of changes adds up to:

| CHANGELOG section | Version part | Example |
|---|---|---|
| **Removed** with a note that existing consumers must adapt | **MAJOR** | `1.0.0`, `2.0.0` |
| **Changed** (breaking) or new top-level feature on the public API | **MINOR** | `0.7.0`, `1.1.0` |
| **Added** of new optional surface, **Fixed**, or no-op maintenance | **PATCH** | `0.6.11` |

While pdip is on `0.x`, **MINOR** is the signal for breaking changes
(as the semver spec allows). Once we reach `1.0`, **MAJOR** is the
only breaking signal.

Examples from recent work:

- ADR-0020 (raise Python floor 3.8 → 3.9) is a **MINOR** bump on
  `0.x`: it is breaking but while we are pre-1.0 we do not bump
  major.
- ADR-0021 and ADR-0022 (driver migrations) are **MINOR** bumps
  because the extras matrix changes and third-party consumers who
  depend on the old driver names have to edit their installs.
- PR #53 (cryptography / Flask / Werkzeug patch and minor bumps)
  is a **PATCH** bump: no pdip API change, transitive maintenance.

### 2. Version source of truth

`setup.py`'s `PYPI_PACKAGE_VERSION` env var stays. Releases happen
by pushing a **git tag** of the form `vMAJOR.MINOR.PATCH` (e.g.
`v0.7.0`) to `main`. The publish workflow reads the tag, strips the
leading `v`, and sets the version.

The tag is **signed** (`git tag -s`) by the releaser. Unsigned tags
do not trigger the publish workflow. (If GPG is not set up for the
releaser, fall back to an annotated tag with a well-known committer
identity; treat this as a gap to close.)

### 3. Release checklist

When cutting a release:

1. Confirm `main` is green on the full CI matrix.
2. Move the **Unreleased** CHANGELOG block to a new section titled
   `[MAJOR.MINOR.PATCH] — YYYY-MM-DD`. Add comparison links at the
   bottom of the file.
3. Bump the default in `setup.py` (`env_version = getenv(..., default='MAJOR.MINOR.PATCH')`)
   so that tagless local builds produce a sane number.
4. Open a PR titled `chore(release): MAJOR.MINOR.PATCH`.
5. Once merged to `main`, tag `vMAJOR.MINOR.PATCH` and push the tag.
6. The publish workflow uploads to PyPI and creates a GitHub
   Release.

### 4. Pre-releases and hotfixes

- Pre-releases are tagged with the usual semver pre-release suffix:
  `v0.7.0rc1`, `v0.7.0b1`. They publish to TestPyPI via
  `python-upload-test-package.yml` only.
- Hotfixes branch from the release tag, land as their own PR, and
  cut a `PATCH` bump from the same branch.

### 5. Yanking

A broken release is yanked from PyPI with an explanatory release
note. No new version is cut solely to replace a yanked version; the
next legitimate bump rolls the fix in.

## Consequences

### Positive

- Consumers can read `CHANGELOG.md` and immediately know which
  version they need for a given fix or feature.
- The git tag is the release boundary; there is no state in the
  repository that contradicts it.
- The mapping between CHANGELOG categories and version parts
  removes the per-release judgement call about "is this breaking?"

### Negative

- The CHANGELOG requires discipline per PR. A PR that silently
  changes public behaviour without touching CHANGELOG is a release
  hazard. Code review has to catch this.
- Pre-release tagging doubles the release types; only one of them
  publishes to the real index. A human mistake (wrong tag shape)
  uploads to the wrong place.

### Neutral

- We stay on `0.x`. A deliberate `1.0` release is its own ADR when
  the API surface stabilises.

## Alternatives considered

### Option A — Continue untracked, cut versions by feel

- **Pro:** Zero policy overhead.
- **Con:** Consumers cannot plan. "Is this bump safe?" has no
  answer.
- **Why rejected:** We just spent an ADR (ADR-0020) removing the
  damage caused by the opposite pattern.

### Option B — Calendar versioning (e.g. `2026.4.0`)

- **Pro:** Release dates are self-documenting.
- **Con:** Does not convey breaking vs non-breaking. Consumers
  have to read every CHANGELOG.
- **Why rejected:** Semver's information density is the whole
  point.

### Option C — Bump version in `setup.py` on every PR

- **Pro:** No env var plumbing.
- **Con:** Every PR becomes a version-bump fight; commits cannot
  be safely cherry-picked.
- **Why rejected:** Tag-based is cleaner.

## Follow-ups

- Cut `v0.7.0` once the dust from the ADR-0017 through ADR-0023
  chain settles. The CHANGELOG Unreleased section already describes
  everything that belongs in it.
- Document the PyPI token rotation schedule (separate security
  ADR).
- Verify the existing `python-upload-package.yml` workflow reads
  the tag correctly. If it does not, fix it as part of the next
  release.

## References

- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)
- [`.github/workflows/python-upload-package.yml`](../../../.github/workflows/python-upload-package.yml)
- [`.github/workflows/python-upload-test-package.yml`](../../../.github/workflows/python-upload-test-package.yml)
- [`setup.py`](../../../setup.py) — `PYPI_PACKAGE_VERSION` env var.
