# ADR-0023: Coverage floor policy

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** testing, ci, quality
- **Extends:** [ADR-0018](./0018-testing-strategy.md)

## Context

[ADR-0018](./0018-testing-strategy.md) deferred the coverage-floor
decision: "We do not pick a headline coverage percentage yet.
Picking a number before the baseline stabilises produces either
vanity (inflated by trivial tests) or friction (blocking useful PRs
behind meaningless tests)."

The baseline has since stabilised enough to choose a number:

- The test harness now gates CI on exit code
  ([#47](https://github.com/ahmetcagriakca/pdip/pull/47)).
- Baseline unit tests landed for the four load-bearing abstractions
  (`Dispatcher`, `Pdi`, pub/sub channel, json helpers).
- Coverage is collected on every job and uploaded as an artefact.

The remaining question is *what* number and *how* to enforce it.

## Decision

### 1. Scope of measurement

Coverage is measured against `pdip/` (already the `--source=pdip`
flag in the CI step), with the following excluded:

- Integration adapters that require external services, under
  `pdip/integrator/connection/types/{sql,bigdata,webservice,file,inmemory,queue}/`.
  These are exercised by `tests/integrationtests/`, which CI does
  not run.
- Parallel execution strategies that depend on a real message
  broker and live subprocesses, under
  `pdip/integrator/integration/types/sourcetotarget/strategies/parallelold/`
  and `parallelthread/`.
- Package `__init__.py` files with no logic.

The exclusion list is encoded in a committed `.coveragerc` so
contributors and CI use the same configuration.

> **2026-04-24 correction:** The ADR originally listed the
> adapter paths without the ``types/`` segment (``pdip/integrator/connection/sql/*``)
> because the policy was drafted before a pass through the actual
> directory layout. The `.coveragerc` was updated to match the
> real paths in the coverage-to-80 PR; coverage measured against
> the corrected exclusion list was 68 % at the time of that PR
> (compared to 47 % with the mislabeled patterns).

### 2. Floor

- **Near-term floor:** `coverage.fail_under = 20`.
- Measured line coverage against the in-scope modules at the time
  this ADR landed was **25 %**. The floor is set one ratchet-step
  below the measurement (rounded down to the nearest `5`) so the
  first normal fluke does not fail an unrelated PR.
- If a PR's coverage drops below the floor, CI fails.
- The floor is a floor, not a target. We want to ratchet up, and
  the starting number is deliberately modest so the ratchet has
  somewhere to go.

### 3. Ratchet policy

- Every six months or after 500 new lines of source (whichever comes
  first), a maintainer issues a brief PR that raises
  `coverage.fail_under` to the current measured number rounded down
  to the nearest `5`.
- Ratchets must be monotonic: the number only goes up.
- Ratchets are **not** architecturally significant changes and do
  not need a full ADR; a PR with `chore(coverage): ratchet to NN`
  and the numbers in the description is enough.

### 4. What does not count

- A test that imports a module but asserts nothing ("smoke" to raise
  the number) is not acceptable. Review flags them.
- Coverage is a floor, not a substitute for meaningful assertions.
  PR review cares about *what* is covered at least as much as
  *how much*.

### 5. CI enforcement

- The existing `coverage report -m` step gains a
  `--fail-under=20`. With `.coveragerc` present, this line is
  redundant but explicit (matches what contributors see locally).
- Coverage artefacts continue to upload so reviewers can diff.

## Consequences

### Positive

- A concrete floor ends the "coverage is nobody's responsibility"
  trap.
- The ratchet turns incremental testing into a ratcheted guarantee
  rather than an ambient hope.
- Integration-only adapters are explicitly out of scope, so unit
  tests cannot be gamed by "we can't run that in CI."

### Negative

- Tests that are added only to keep the floor up are a real risk.
  We rely on code review to catch them; this ADR cannot.
- Raising `fail_under` makes the rare flaky test a PR-blocker.
  Flakes are to be fixed, not silenced by lowering the bar.

### Neutral

- The initial `55` is deliberately modest. The ratchet is the
  discipline; the starting number is less important.

## Alternatives considered

### Option A — No enforcement, coverage stays informational

- **Pro:** No blocker.
- **Con:** Means trend lines and artefacts with no consequence.
- **Why rejected:** The existing gap between "we collect coverage"
  and "we care about coverage" is exactly what this ADR closes.

### Option B — Very high floor (80 %+) immediately

- **Pro:** Sounds rigorous.
- **Con:** Forces a bulk of trivial tests against modules that
  already work; blocks valuable PRs for no safety reason.
- **Why rejected:** Vanity metric; ADR-0018 already warned about
  this shape.

### Option C — Diff coverage only (every PR holds its own line)

- **Pro:** Avoids big-bang and matches PRs to their author.
- **Con:** A PR that touches zero lines can merge; coverage slowly
  erodes around unmodified areas as dead code grows.
- **Why rejected:** The ratcheting floor handles this more
  transparently.

## Follow-ups

- Add `.coveragerc` with the exclusion list in the implementation
  PR.
- Extend CI's coverage step with `--fail-under=55`.
- File a "coverage ratchet" reminder in six months.
- If the floor ever needs to go *down* (e.g. a large module move
  one-time dips the number), it is done via a one-shot ADR, not by
  an edit.

## References

- [`.coveragerc`](../../../.coveragerc) — to be added in the
  implementation PR
- [`.github/workflows/package-build-and-tests.yml`](../../../.github/workflows/package-build-and-tests.yml)
- [ADR-0018](./0018-testing-strategy.md)
