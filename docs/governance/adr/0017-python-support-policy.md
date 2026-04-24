# ADR-0017: Python support matrix is set by `python_requires`, not by dependency drift

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** packaging, compatibility

## Context

pdip advertises its supported Python versions in two places:

- [`setup.py`](../../setup.py) — `python_requires=">=3.8"` and a matching
  set of `Programming Language :: Python :: ...` classifiers.
- [`.github/workflows/package-build-and-tests.yml`](../../.github/workflows/package-build-and-tests.yml)
  — a CI matrix that currently runs `3.9`, `3.10`, `3.11`.

Dependabot occasionally opens pull requests that look like routine
version bumps but, in their changelogs, quietly drop support for a
Python version pdip still promises. Merging such a PR would break
existing consumers on that Python without any signal in the pdip
version number.

The immediate trigger for this ADR is PR #37
(`mysql-connector-python` 8.4.0 → 9.1.0). Its 9.0 release removes
Python 3.8 support. pdip still supports Python 3.8 at the package
level, so merging would silently break the `integrator` extra for
3.8 users.

## Decision

The list of Python versions that pdip officially supports is owned by
**pdip**, not by any individual dependency.

Concretely:

1. `setup.py`'s `python_requires` is the authoritative declaration.
2. We do **not** accept a dependency upgrade whose release notes drop
   a Python version inside our supported window unless the same change
   set also raises `python_requires` — which itself requires an ADR
   (see the process below).
3. Raising the minimum supported Python is a **minor version** bump
   for pdip, called out in `CHANGELOG.md` under a dedicated
   **Removed** subsection, and backed by an ADR that documents:
   - why the drop is worth it,
   - which downstream consumers are plausibly affected,
   - the date from which the older Python is unsupported.
4. When a Dependabot PR violates rule 2, we comment with a link back
   to this ADR and either:
   - pin the dependency to the last version that still supports our
     floor, or
   - close the PR and open a deliberate ADR to raise the floor.

## Consequences

### Positive

- Consumers pinned to a specific Python get breakage only when we
  say so, not when a transitive maintainer says so.
- The matrix in CI, the `python_requires` declaration, and the
  classifiers are kept in lockstep on purpose.
- "We're dropping Python X" becomes a visible, auditable event
  instead of a side effect.

### Negative

- We occasionally have to stay on an older major of a dependency.
  For `mysql-connector-python` in particular this means staying on
  8.x until we decide to drop Python 3.8.
- Reviewers of Dependabot PRs must read release notes far enough to
  notice a support drop. This ADR makes it cheap: spot it, link here,
  close or pin.

### Neutral

- CI's current matrix (`3.9`, `3.10`, `3.11`) is narrower than the
  declared floor (`>=3.8`). That is a separate conversation; this ADR
  does not change CI.

## Alternatives considered

### Option A — Always merge Dependabot bumps

- **Pro:** Zero-effort security posture.
- **Con:** Silently breaks supported Python versions the first time a
  dependency drops one.
- **Why rejected:** Unacceptable trade-off; our support matrix stops
  meaning anything.

### Option B — Remove `python_requires` and let pip resolve

- **Pro:** Users discover support implicitly.
- **Con:** The discovery happens at install time on the user's
  machine, not at our release time. Failures are attributed to pdip
  anyway.
- **Why rejected:** Bad user experience.

### Option C — Treat each Dependabot support drop as ad-hoc

- **Pro:** Flexibility.
- **Con:** Inconsistent decisions over time.
- **Why rejected:** An ADR-backed rule is cheaper than re-arguing it
  every few months.

## Follow-ups

- Apply this rule to the outstanding PR #37 by closing it and pinning
  `mysql-connector-python==8.4.0` until an ADR raises the Python
  floor.
- Consider expanding the CI matrix to include `3.8` so that a
  regression on the floor is caught in CI instead of post-release.
- When a future ADR raises the minimum Python, reopen the
  `mysql-connector-python` upgrade.

## References

- [`setup.py`](../../setup.py)
- [`.github/workflows/package-build-and-tests.yml`](../../.github/workflows/package-build-and-tests.yml)
- [`docs/governance/security-audit-2026-04-24.md`](../security-audit-2026-04-24.md)
- PR #37: <https://github.com/ahmetcagriakca/pdip/pull/37>
