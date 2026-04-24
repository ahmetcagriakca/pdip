# ADR-0020: Raise `python_requires` floor from 3.8 to 3.9

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** packaging, compatibility, python
- **Supersedes floor declared in:** [ADR-0017](./0017-python-support-policy.md)
  (the policy itself stands; this ADR is its first deliberate exercise.)

## Context

pdip's `setup.py` declares `python_requires=">=3.8"` and carries a
`Programming Language :: Python :: 3.8` classifier. In reality the CI
matrix (see [ADR-0019](./0019-python-314-adoption.md)) runs
`3.9 / 3.10 / 3.11 / 3.12 / 3.13` blocking and `3.14` non-blocking.
Python 3.8 has **never** been in the matrix. We are advertising a
version we do not test.

Two further pressures point the same way:

- **Python 3.8 reached end-of-life on 2024-10-07.** It receives no
  security updates upstream. Supporting it in a framework that lands
  new code today is actively harmful; users on 3.8 get whatever we
  ship unless it happens to still parse.
- **Dependency drift.** Several bumps we want to merge are blocked
  only by 3.8 support — most visibly
  `mysql-connector-python` 9.x (Dependabot PR #37 was declined
  under ADR-0017 precisely because of this). Every such block delays
  a real security or feature upgrade.

[ADR-0017](./0017-python-support-policy.md) requires a deliberate,
ADR-gated act to narrow the floor. This is that act.

## Decision

The supported Python matrix is raised by one step:

- `setup.py` → `python_requires=">=3.9"`.
- `Programming Language :: Python :: 3.8` classifier removed.
- CI matrix stays as declared in ADR-0019 (3.9–3.13 blocking, 3.14
  non-blocking).
- `CHANGELOG.md` records the drop under a **Removed** section.
- This is a **minor** version bump for pdip, per semver for a
  meaningful reduction in supported surface.

No further Python floors are raised by this ADR. 3.9 stays in the
matrix; dropping 3.9 next would be its own decision.

## Consequences

### Positive

- The advertised floor matches the tested floor. No silent gap.
- Unblocks dependency bumps whose only cost was 3.8 support
  (`mysql-connector-python` 9.x being the immediate one).
- Users on an EOL runtime are informed rather than silently served
  a package whose internals may not actually run.

### Negative

- Any consumer still on 3.8 must either stay on pdip `0.6.x` or
  upgrade their runtime. The upgrade to 3.9 is trivial in practice
  but is a breaking change in kind.
- `setup.py`'s `install_requires` has a `dataclasses==0.6` historical
  pin already removed in [#46](https://github.com/ahmetcagriakca/pdip/pull/46),
  so no further `install_requires` editing is needed.

### Neutral

- The `dataclasses` stdlib module (always present on 3.7+) remains
  used throughout pdip; nothing in the codebase actually relied on
  the 3.8 runtime anyway.

## Alternatives considered

### Option A — Keep 3.8 and add it to the CI matrix

- **Pro:** Promise kept as stated.
- **Con:** Committing CI minutes to an EOL runtime; we would still
  be building for a line that upstream no longer patches.
- **Why rejected:** Serving 3.8 as a first-class target is a cost
  without a user we can point to.

### Option B — Jump to 3.10 or 3.11

- **Pro:** Drops more versions in one ADR; enables PEP 604 union
  syntax (`X | Y`), `ExceptionGroup`, etc.
- **Con:** Each step drops real users. Without a concrete need we
  cannot justify two drops at once.
- **Why rejected:** ADR-0017 wants explicit, needs-driven drops.
  3.9 is the immediate need; 3.10+ is a future conversation.

### Option C — Re-phrase the floor as "best effort ≥ 3.8"

- **Pro:** Minimal disruption.
- **Con:** "Best effort" is invisible to pip. Users still install,
  still crash.
- **Why rejected:** Promises must be testable.

## Follow-ups

- Reconsider `mysql-connector-python` 9.x now that 3.8 is no longer
  in scope. (Was PR #37, previously declined per ADR-0017.) A fresh
  Dependabot PR or a manual bump is fine.
- Update the README's "Python 3.8+" note to "Python 3.9+".
- Delete the 3.8 row from any install-matrix table we publish.

## References

- [`setup.py`](../../../setup.py)
- [ADR-0017](./0017-python-support-policy.md)
- [ADR-0019](./0019-python-314-adoption.md)
- [PEP 602 — Python release cadence](https://peps.python.org/pep-0602/)
- Python 3.8 end-of-life announcement.
