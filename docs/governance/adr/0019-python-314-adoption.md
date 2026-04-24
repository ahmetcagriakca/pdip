# ADR-0019: Python 3.14 adoption plan

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** packaging, compatibility, python

## Context

Python 3.14 is the current release line (released October 2025). pdip
advertises `python_requires >= 3.8`, but its CI matrix only tests
`3.9 / 3.10 / 3.11`. That leaves two gaps at once:

1. The **floor** (3.8) is claimed but unverified.
2. The **ceiling** stops two releases below current Python.

Consumers increasingly run on 3.12 and 3.13. Without CI coverage we
ship blind to them. 3.14 adds PEP 649 lazy annotation evaluation and
further tightens deprecations in `asyncio`, `ssl`, `logging`, and
`unittest`; we need to know whether pdip breaks under it *before* a
user finds out for us.

[ADR-0017](./0017-python-support-policy.md) says the supported matrix
is owned by pdip and not narrowed by dependency drift. This ADR is
the first deliberate use of that rule: we are widening the matrix,
not narrowing it.

## Decision

The Python 3.14 adoption is **staged** and CI-gated.

### Stage 0 — safety net (prerequisite)

[ADR-0018](./0018-testing-strategy.md) fixes the test harness so red
tests actually fail the build. Nothing below this line is safe to do
without Stage 0.

### Stage 1 — widen the matrix

The CI matrix in `.github/workflows/package-build-and-tests.yml`
expands to:

```
python: [ '3.9', '3.10', '3.11', '3.12', '3.13', '3.14' ]
```

New jobs may be added as **non-blocking** (`continue-on-error: true`)
the first time a Python version lands so the team sees failures
without blocking merges during triage. As soon as the job is green
for a release cycle, it becomes blocking.

### Stage 2 — fix compatibility issues

Any failures surfaced by the new matrix rows are fixed in focused
PRs, each referencing this ADR. Expected hotspots:

- `pdip.integrator.pubsub.*` and `pdip.processing.*` — `multiprocessing`
  changed default start methods and semantics across 3.12 → 3.14.
- `dataclass_json` usage — Python 3.14 enforces stricter generic
  behaviour; if `dataclasses-json` lags, we pin to a known-good
  release.
- Deprecation warnings now raising in 3.14 (`pkgutil.find_loader`,
  `typing.io`, a few `importlib` shims).

Each fix keeps **backward compatibility** with the existing floor
(3.9). We only raise `python_requires` in Stage 4, and only by ADR.

### Stage 3 — dependency readiness

Some dependencies do not ship 3.14 wheels yet or have known issues.
Handle per package in the audit at
[`docs/governance/security-audit-2026-04-24.md`](../security-audit-2026-04-24.md):

- `pandas 2.2.x` — confirm wheels for 3.13 and 3.14.
- `cx_Oracle 8.3.0` — unlikely to gain 3.14 support; plan migration
  to `python-oracledb` (separate ADR).
- `kafka-python 2.0.2` — stagnant; plan replacement to
  `kafka-python-ng` or `confluent-kafka` (separate ADR).
- `mysql-connector-python 8.4.0` — stops at Python 3.8 support;
  upgrading to 9.x requires a deliberate raise of
  `python_requires` (see Stage 4).
- `func-timeout`, `injector`, `SQLAlchemy`, `Flask` family,
  `cryptography` — expected to cope with 3.14 within their current
  pinned versions; verify in CI.

If a dependency blocks 3.14 and has no drop-in replacement, we
document the blocker on this ADR and mark 3.14 CI as
non-blocking until the upstream fix lands.

### Stage 4 — floor decision

**Separate ADR.** Only after 3.14 is a blocking CI job for a release
cycle do we decide whether to raise `python_requires`. The trigger
condition is "we want to merge a bump that requires a newer floor"
(e.g. `mysql-connector-python` 9.x). Raising the floor is a breaking
change for consumers and ships with a **MINOR** version bump, a
`CHANGELOG.md` **Removed** entry, and a new ADR.

### Stage 5 — drop old versions

Same shape as Stage 4: only when a concrete need justifies it.
Dropping 3.9 has no intrinsic value; it has value only when it
unblocks a dependency or language feature we actually want.

## Consequences

### Positive

- Users on 3.12 / 3.13 / 3.14 have a signal that we test against
  their runtime.
- We find out about breakage when *we* do, not when they do.
- Dependency decisions (the mysql-connector case) stop being one-off
  judgement calls and become part of an explicit staging.

### Negative

- CI jobs and minutes roughly double.
- Some third-party packages may not have 3.14 wheels; those jobs
  will red-flag until upstream ships.
- A non-blocking 3.14 job during Stage 1 means "we know it's red and
  it's okay." That requires discipline; red jobs tend to get
  ignored.

### Neutral

- The floor stays at 3.8 *by declaration* until Stage 4. In practice
  we will have CI proof only for 3.9 and up. That mismatch is
  acknowledged; users on 3.8 are on their own until we decide.

## Alternatives considered

### Option A — jump straight to 3.14, drop 3.9

- **Pro:** Smallest matrix.
- **Con:** Breaks existing consumers without warning.
- **Why rejected:** ADR-0017 forbids it; breaking changes need an
  ADR of their own.

### Option B — wait for every dependency to support 3.14 before
adding the job

- **Pro:** All-green from day one.
- **Con:** We find out about pdip's *own* 3.14 issues only after
  every upstream has moved. Too slow.
- **Why rejected:** Non-blocking jobs give us the signal without
  blocking other work.

### Option C — skip 3.12 and 3.13, test only 3.14

- **Pro:** Fewer jobs.
- **Con:** Two unvalidated versions between our CI floor and 3.14.
  Users on 3.12 or 3.13 are invisible to us.
- **Why rejected:** Cheap to add two jobs; huge information gain.

## Follow-ups

- PR adding 3.12, 3.13, 3.14 to the matrix (with 3.14 non-blocking
  if needed).
- Per-dependency PRs from Stage 3.
- New ADR when Stage 4 is triggered.

## References

- [`.github/workflows/package-build-and-tests.yml`](../../../.github/workflows/package-build-and-tests.yml)
- [`setup.py`](../../../setup.py)
- [ADR-0017](./0017-python-support-policy.md)
- [ADR-0018](./0018-testing-strategy.md)
- [Security audit](../security-audit-2026-04-24.md)
- [Python 3.14 release notes](https://docs.python.org/3.14/whatsnew/3.14.html)
