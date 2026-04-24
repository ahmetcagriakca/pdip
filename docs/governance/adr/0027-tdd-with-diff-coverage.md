# ADR-0027: Test-first development (TDD) with diff-coverage enforcement

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** testing, ci, quality, process
- **Extends:** [ADR-0018](./0018-testing-strategy.md) (testing strategy),
  [ADR-0023](./0023-coverage-floor-policy.md) (coverage floor),
  [ADR-0026](./0026-test-quality-rules.md) (test quality rules)

## Context

The repository's coverage floor has ratcheted from "uncollected" →
20 % → 30 % → 95 %. At 95 %, further progress **by raw test volume
alone** starts to erode quality:

- Writing tests *after* the code tends to rubber-stamp the
  implementation — the test reflects what the code does, not what
  the behaviour should be.
- Coverage-chasing after the fact rewards volume over meaning.
  ADR-0026 codifies behavioural-assertion rules; combining those
  with test-first removes the "cover this last line" trap.
- At 95 %, the remaining 5 % is exactly the code most likely to
  hide bugs: defensive guards, error paths, dead branches from
  earlier bugs. Test-first forces a reader to ask "what is the
  expected behaviour here?" before accepting the implementation.

The natural next step is **TDD** — write the failing test first,
then the implementation that makes it pass — and enforce it
mechanically where possible.

## Decision

### 1. TDD is the default workflow for new production code

When adding or modifying a public behaviour in `pdip/`:

1. **Write the failing test first.** The test should describe the
   behaviour in its name and assert it in its body (ADR-0026 rules
   apply verbatim).
2. **Run the test and confirm it fails for the right reason** —
   either the code does not exist yet, or the current code does
   the wrong thing. A test that passes against unchanged code is
   not TDD.
3. **Write the smallest change that makes the test pass.** No
   extra behaviour; no speculative hooks.
4. **Refactor** if needed; every test must keep passing.
5. **Commit.** Each commit is either red-green (new failing test
   + code that makes it pass) or pure refactor.

### 2. Exceptions

TDD is not required for:

- Pure configuration changes (YAML, env defaults, CI workflows,
  ADR documents).
- Test fixtures and test helper code (the tests themselves ARE
  the specification).
- Trivial rename / reformat refactors that do not change behaviour
  (but the test must exist and keep passing).
- Bug fixes where a test already exists that pins the current bad
  behaviour; update the test first to assert the desired behaviour,
  watch it fail, then fix the code (this is still test-first).

Everything else that touches `pdip/` follows TDD.

### 3. Machine enforcement — diff-coverage

ADR-0023's `fail_under` enforces total coverage. It does **not**
catch a PR that leaves its own new lines untested. We add a second
gate:

- `diff-cover` (or an equivalent tool) is added to CI.
- Every PR runs `diff-cover` against `origin/main`. The tool
  reports the coverage percentage **of lines changed in the PR**.
- The CI step enforces **100 % diff coverage**: a PR whose newly
  added or modified `pdip/` lines are not covered by the same PR's
  test changes fails.
- Test and config files (`tests/`, `*.yml`, `*.yaml`, `*.md`,
  `*.cfg`, `*.toml`, `.coveragerc`, `.gitignore`) are excluded
  from the diff-coverage numerator.

This means: a PR that adds a new method to a service class without
a test for it fails CI, even if the overall floor stays at 95 %.

### 4. Machine enforcement — test-first signal

A perfectly rigorous "the test commit is older than the
implementation commit" check is brittle (rebases, squash merges
rewrite history). We approximate it:

- Every PR's commit graph must contain **at least one commit whose
  diff adds a `test_*` method or a new `Test*` class** before any
  commit that grows the statement count of `pdip/`. `diff-cover`'s
  100 % gate catches the outcome; this ordering check is a soft
  reviewer signal, not a CI hard-fail. If a PR's history is
  squashed before merge, the ordering evidence lives in the PR's
  commit list rather than the final `main` history.
- Reviewers are expected to ask "is there a commit here where the
  test fails without the impl?" when the ordering is not obvious.

### 5. 100 % overall coverage as the new target

With diff-coverage in place and the quality-guard rules from
ADR-0026 already enforced, **overall coverage can be raised to
100 %** safely:

- No vanity tests get past review (ADR-0026 A.2, E.1).
- No uncovered new line gets past CI (diff-cover).
- No silent fail (ADR-0018 exit-code gate).
- Unreachable defensive code that cannot be triggered from outside
  is marked with `# pragma: no cover` and a **one-line comment
  explaining why** on the same line. The guard refuses a pragma
  without a comment.

The ratchet to 100 happens in its own PR after the existing
flagged bugs are fixed (they are the cause of most of today's 5 %
gap).

### 6. Review expectations

Reviewers check, in order:

1. The PR contains a test that describes the new behaviour and
   (at some commit) fails against the unchanged code.
2. CI is green — including `diff-cover` at 100 %.
3. Every `# pragma: no cover` added in the PR has a one-line
   reason comment on the same line.
4. ADR-0026 rules hold (quality_guard already covers the
   machine-checkable ones).

## Consequences

### Positive

- The "write tests second" trap that produces rubber-stamp tests
  is closed.
- Every new line ships with a test that describes its purpose.
- The 100 % overall floor is defendable — it stops being "how much
  code do we inspect?" and becomes "how much behaviour do we
  specify?"
- Agent-written code is subject to the same gate as human-written
  code.

### Negative

- PR feedback loops include the diff-cover step; a forgotten test
  fails CI.
- Pragma hygiene is now part of review. Missed pragma comments
  are a review nit reviewers have to catch until we build a guard
  for them.
- TDD is a habit, not a syntax rule. Review still carries the
  ordering-signal check.

### Neutral

- The `fail_under` overall floor and the diff-cover PR gate are
  independent mechanisms: one guards the body, one guards the
  edges.

## Alternatives considered

### Option A — Stay at 95 %, no diff-cover

- **Pro:** Zero new tooling.
- **Con:** Any new module can drop the effective coverage of its
  own file to 0 % without the total moving below 95 %.
- **Why rejected:** Large additions create gaps the total hides.

### Option B — Enforce mutation testing instead of TDD

- **Pro:** Catches tests that do not actually assert the mutated
  line.
- **Con:** 10× more CI time, needs tool ramp-up, no equivalent
  "write the test first" push.
- **Why rejected:** Worth considering later; TDD+diff-cover
  covers the day-one concern.

### Option C — Require a literal `test-*` commit before an `impl-*`
commit

- **Pro:** Objective.
- **Con:** Squash-merge and rebase rewrite history; does not
  survive merge. Makes local workflow rigid without clear payoff.
- **Why rejected:** Soft reviewer signal is enough; diff-cover
  is the hard gate.

## Follow-ups

- Bug-fix PR that closes the flagged dead-code causers so their
  lines become legitimately coverable.
- `# pragma: no cover`-with-comment guard added to
  `tests/unittests/quality_guard/test_conventions.py`.
- Ratchet PR that moves `fail_under` from 95 to 100.

## References

- [`.github/workflows/package-build-and-tests.yml`](../../../.github/workflows/package-build-and-tests.yml)
  — `diff-cover` step added in the implementation PR.
- [`.coveragerc`](../../../.coveragerc).
- [ADR-0018](./0018-testing-strategy.md), [ADR-0023](./0023-coverage-floor-policy.md),
  [ADR-0026](./0026-test-quality-rules.md).
- [diff-cover](https://github.com/Bachmann1234/diff_cover) — the tool
  the CI step uses.
