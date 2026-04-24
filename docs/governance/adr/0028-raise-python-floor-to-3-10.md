# ADR-0028: Raise `python_requires` floor from 3.9 to 3.10

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** packaging, compatibility, python, ci
- **Supersedes:** the floor half of [ADR-0020](./0020-raise-python-floor-to-3-9.md)
- **Related:** [ADR-0017](./0017-python-support-policy.md),
  [ADR-0019](./0019-python-314-adoption.md),
  [ADR-0023](./0023-coverage-floor-policy.md)

## Context

Following [ADR-0020](./0020-raise-python-floor-to-3-9.md) the CI
matrix ran Python `3.9, 3.10, 3.11, 3.12, 3.13, 3.14`. While
ratcheting coverage to 100 % (see [ADR-0023](./0023-coverage-floor-policy.md)
ratchet history) we hit a practical wall on Python 3.14:

- `coverage xml` and `coverage html` in `coverage.py 7.6.12` fail on
  the 3.14 matrix cells (ast-module changes in the 3.14 pre-release
  reporters).
- The first version of `coverage.py` that both handles 3.14 cleanly
  *and* ships a 3.14 classifier is `7.11.0`, which raised
  `requires_python` to `>= 3.10`.
- No single coverage release simultaneously supports our declared
  floor (3.9, per ADR-0020) and Python 3.14 XML generation.

Dependency surveying confirmed this is not a one-off: several
libraries in our direct and transitive chain (SQLAlchemy 2.1,
cryptography ≥ 47, PyYAML 7.x work-in-progress,
`dataclasses-json` minor updates) are normalising on `>= 3.10` and
dropping 3.9 support. Staying on 3.9 means either stale
dependencies or chains of workarounds that increase review burden.

Meanwhile, Python 3.9 reached end-of-life upstream on **2025-10-05**
(per [PEP 596](https://peps.python.org/pep-0596/)): it no longer
receives security fixes, and the Python Software Foundation's
[supported versions list](https://devguide.python.org/versions/)
marks it as **end-of-life**.

Running unit tests against an EOL runtime is a declared signal of
support we can no longer honour; the CI cells pass, but we can't
realistically ship fixes for 3.9-specific regressions because we
can't pull in upstream fixes that require 3.10+ either.

## Decision

The supported Python matrix is raised by one step:

- `setup.py` → `python_requires=">=3.10"`.
- `Programming Language :: Python :: 3.9` classifier removed.
- CI matrix drops `3.9`; new declared range is **3.10–3.14**
  (five versions, Linux/macOS/Windows, 15 cells).
- `coverage==7.6.12` pin is replaced with `coverage==7.13.5`
  (current stable), which requires `>= 3.10`.
- The `fail_under = 100` gate stays on the canonical 3.11 ubuntu
  cell per ADR-0023 §5.
- `coverage xml` continues to be scoped to the canonical cell.
  Empirical note from PR #87 CI: coverage 7.13.5 still fails the
  XML reporter on all three 3.14 matrix cells (ubuntu, macos,
  windows) even though its trove classifiers list 3.14. The
  failure is invisible to the `output` field of the check-run
  API and the workflow logs API is admin-only, so the exact
  stack trace remains opaque. The canonical-cell scoping from
  PR #84 stays in force as a pragmatic mitigation; a follow-up
  investigation can revisit it if a future `coverage.py` release
  or a 3.14 stdlib patch removes the symptom.
- This is a **minor** version bump for pdip, per semver for a
  meaningful reduction in supported surface.

No further Python floors are raised by this ADR. 3.10 stays in the
matrix; dropping 3.10 next would be its own decision.

## Consequences

### Positive

- The advertised floor matches an in-support upstream runtime.
- Unblocks `coverage.py` ≥ 7.11 and the stream of 3.10+-only
  library bumps that have been piling up behind the floor.
- Reduces the surface of workarounds: 3.9-specific compatibility
  shims elsewhere in the tree (Python floor assumptions in
  `type_checker`, `multiprocessing` context pinning) can be
  simplified in follow-up PRs.

### Negative

- Any consumer still on 3.9 must either stay on pdip `0.7.x` or
  upgrade their runtime. The upgrade to 3.10 is non-breaking in
  practice (match-case is additive, stdlib changes are mostly
  additive) but is a breaking change in kind — hence the MINOR
  version bump and the **Removed** entry in CHANGELOG.
- One less cell of Python-version-specific test coverage.

### Neutral

- No change to the coverage target or the `fail_under = 100`
  enforcement. ADR-0023 remains in force; only the canonical cell
  composition is unchanged.

## Alternatives considered

### Option A — Keep 3.9 and accept stale `coverage.py`

- **Pro:** No consumer churn.
- **Con:** Every ecosystem bump for the next year has to be
  evaluated for 3.9 compatibility, including security releases.
  `coverage.py` 7.6.12 never ships a fix for 3.14 XML generation —
  we either keep the canonical-cell workaround forever or pin to a
  version that silently regresses.
- **Why rejected:** We are already paying the cost of workarounds
  (PR #84, PR #85 investigation). Dropping an EOL runtime is
  cheaper long-term than extending it.

### Option B — Keep 3.9 and run `coverage` from a local fork

- **Pro:** Preserves the floor.
- **Con:** Maintaining a fork of `coverage.py` is not a thing a
  small framework should take on.
- **Why rejected:** Obviously out of scope.

### Option C — Jump the floor to 3.11 directly

- **Pro:** Matches the canonical test cell.
- **Con:** Drops 3.10, which is still in support (EOL 2026-10).
- **Why rejected:** 3.10 is still supported upstream and by the
  full dependency chain; no reason to drop it yet. 3.10 is the
  immediate need; 3.11+ would be a future conversation.

## Follow-ups

- Update the README's "Python 3.9+" note to "Python 3.10+".
- Delete the 3.9 row from any install-matrix table we publish.
- Drop the ``Programming Language :: Python :: 3.9`` classifier
  from `setup.py`.
- Bump `coverage` to `7.13.5` in `requirements.txt` and verify
  the full suite.
- Record the drop under a **Removed** section in `CHANGELOG.md`
  alongside this ADR.
- Keep the canonical-cell scoping for `coverage xml` from PR #84
  in place; revisit once a future coverage.py release surfaces
  a reproducible fix for the 3.14 XML reporter failure. Track
  this as a separate follow-up issue.

## References

- ADR-0017 — Python support policy.
- ADR-0019 — Python 3.14 adoption.
- ADR-0020 — Raise `python_requires` floor from 3.8 to 3.9
  (superseded for the floor decision).
- ADR-0023 — Coverage floor policy.
- PR #84 — canonical-cell workaround for `coverage xml` on 3.14.
- PR #85 (closed) — investigation confirming no single
  `coverage.py` version supports both 3.9 and 3.14 XML generation.
- Python 3.9 end-of-life notice (PEP 596, 2025-10-05).
