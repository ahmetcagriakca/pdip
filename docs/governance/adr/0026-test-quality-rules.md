# ADR-0026: Test quality rules

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** testing, ci, quality
- **Extends:** [ADR-0018](./0018-testing-strategy.md) (testing strategy)
  and [ADR-0023](./0023-coverage-floor-policy.md) (coverage floor).

## Context

[ADR-0018](./0018-testing-strategy.md) set up the pyramid, the CI
gate, the priority order for closing coverage gaps, and
[ADR-0023](./0023-coverage-floor-policy.md) locked in a ratcheting
floor. Those ADRs answered **what** to test and **how much**. They
did **not** answer **how** a test should be written.

Since ADR-0018 landed, the suite grew from 24 runs to 112 runs. Along
the way, five real bugs surfaced *because* the tests asserted the
right things:

- `Repository.delete` generated a UUID object on non-Postgres
  dialects, breaking SQLite binding.
- `test_process_error` hard-coded `results[0]` instead of iterating
  `results`, so the assertion only held under fork ordering.
- 28 `E711` / `E712` / `E722` real-bug markers.
- `MessageBroker.unsubscribe` had an operator-precedence bug that
  made the "unknown event" warning path dead code.
- `ChannelQueue` had no non-blocking public accessor; tests reached
  past it.

None of those bugs would have surfaced with "it doesn't raise" tests.
Every one needed a test that asserted a specific *behaviour*. This
ADR codifies the rules that produced that outcome so future tests
land with the same quality, not whatever each author felt like
writing.

Random test-writing is out. Quality-first is in, and the bar is
enforced by a mix of CI-level machine checks and review-time rules.

## Decision

### A. Intent

**A.1** Every `test_*` method asserts at least one concrete behaviour.
No "does-not-raise" tests unless *not raising* is literally the
behaviour under test — and in that case the test documents it in a
short comment.

**A.2** No tautological assertions. `assertTrue(True)`, `assert True`,
`assertEqual(x, x)` and their cousins are forbidden. They pass but
prove nothing.

**A.3** Test method names describe the behaviour, not the subject
alone. Pattern: `test_<subject>_<behaviour>[_when_<condition>]`.
Generic names (`test_happy_path`, `test_1`, `test_it_works`) are
rejected at review.

**A.4** Test **class** names describe the behaviour group, not the
subject in isolation. `DispatcherFindsHandlerByConvention` is
preferred to `TestDispatcher`. `TestSubject` is acceptable when the
class holds tests for one concrete behaviour group and the group's
shape is obvious from context.

**A.5** Every public method of a production class with a **documented
error path** has at least one negative test. "The happy path works"
is half the contract.

### B. Structure

**B.1** **Arrange / Act / Assert.** Each test reads top-to-bottom as
three clearly separated blocks. Blank lines between the phases are
strongly encouraged.

**B.2** **One behaviour per test method.** If a test needs more than
one `assert*` for *different* properties of the *same* behaviour, that
is fine. If the second assertion is really a second test, split.

**B.3** **Fixture factories, not magic dicts.** Recurring
construction lives in a helper at the top of the test module
(`_build_config(...)`, `_install_stubs()`). Inline magic dicts
repeated across tests are rejected.

**B.4** **Mocks for boundaries only.** Do not mock the class under
test. Mock its collaborators. If a test mocks the subject, it is
testing the mock, not the code.

### C. Isolation

**C.1** Tests do not share mutable state. `setUp` / `tearDown` reset
any class-level cache touched by the test. Module-level mutable
state (e.g. `JsonConvert.mappings`) is snapshotted and restored.

**C.2** Stubs placed in `sys.modules` are **restored** before the test
module's own import block completes. The Oracle (ADR-0021), Kafka
(ADR-0022), and MySQL tests set this pattern; all new stub-using
tests follow it.

**C.3** A test's outcome does not depend on execution order. Tests
must pass in any order the runner chooses. A meta-test shuffles
test modules in CI to surface order dependencies. (Shuffle support
is a follow-up; the rule still applies at review.)

### D. Determinism

**D.1** No `time.sleep` over 0.1 s in unit tests. If the code under
test genuinely has a time component, test it with an injectable
clock, not a wall-clock wait.

**D.2** No network, no real filesystem, no external services in
unit tests. File I/O is limited to `tempfile` paths created and
torn down inside the test.

**D.3** Randomness is seeded. A test that calls `random.*`,
`uuid.uuid4()` without seeding, or any similar source is deterministic
by construction or it is rejected.

**D.4** No assertions on wall-clock timing. "Completes in under X"
style tests belong in a separate performance suite, not the unit
suite.

### E. Coverage

**E.1** A test whose only purpose is to raise the coverage number is
rejected. `from pdip.x import y` without a behavioural assertion is
not a test.

**E.2** The coverage floor is set by [ADR-0023](./0023-coverage-floor-policy.md)
and ratcheted per that ADR's rules. This ADR does not change the
number; it forbids gaming it.

### F. Framework

**F.1** `unittest` only, per ADR-0018. No `pytest.fixture`, no
`pytest.mark`, no `conftest.py` magic. Contributors who prefer
`pytest` can still *run* `pytest tests/unittests`; what they cannot
do is *write* tests in that style.

**F.2** **No star imports** anywhere under `tests/`.

**F.3** Unit tests never boot `Pdi()`. The DI container is for
integration-style tests (the `basic_app_*` suites). Smaller units
(`Dispatcher`, `Repository`, `IntegrationExecution`, connectors)
are exercised in isolation.

### G. Enforcement

**G.1** **Machine-checked rules** are enforced by a meta-test in
`tests/unittests/quality_guard/test_conventions.py` that runs as
part of every CI build. The rules it checks today:

- Every `test_*` method contains at least one `assert` statement
  (AST-level). (A.1)
- No `assertTrue(True)`, `assert True`, `assertFalse(False)`, or
  `assertEqual(x, x)` tautologies. (A.2)
- No `from X import *` in any `tests/` file. (F.2)
- No `time.sleep(N)` with `N >= 0.1` in unit tests. (D.1)
- No `from pytest` / `import pytest` in any test file. (F.1)

Violations make the guard fail, which exits `run_tests.py` non-zero,
which fails CI.

**G.2** **Review-checked rules** — everything above that a machine
cannot easily verify (naming, AAA structure, shared state, negative
paths) — is on the reviewer. The PR template references this ADR;
reviewers comment with the rule number that a change violates.

**G.3** **Exceptions** to any rule require a one-line comment on the
offending test linking to this ADR and a short reason. Blanket
exceptions live in the guard module's allow-list with an inline
comment. We accept a trickle of exceptions; we do not accept
silent drift.

## Consequences

### Positive

- Reviewers have rules to point at, not vibes.
- Machine-enforced rules catch the five most common anti-patterns
  without human attention.
- Tests that find bugs (like the five we have already caught)
  outnumber tests that exist only to raise a number.
- The quality bar is the same for human-written and agent-written
  tests.

### Negative

- Adding a test is slightly slower than "any test is a good test."
- The guard has its own maintenance cost — a rule that is too
  strict has to be relaxed with an ADR update, not a silent edit.
- Some useful patterns (property-based tests via `hypothesis`,
  pytest fixtures) stay off the table until a future ADR revisits.

### Neutral

- The guard does not replace review. It catches the easy stuff so
  review attention goes to the hard stuff.

## Alternatives considered

### Option A — Rely on review only

- **Pro:** No machine rules to maintain.
- **Con:** The five most common anti-patterns have been landing in
  the field for years under pure-review projects. Humans miss
  them. Machines do not.

### Option B — Adopt a linter plugin (flake8-aaa, pylint-test)

- **Pro:** Off-the-shelf.
- **Con:** They assume pytest. We are on unittest by ADR-0018.
  Adapting them costs more than the ~100 lines of meta-test.

### Option C — Switch to pytest and gain its fixture / parametrize
plugins

- **Pro:** The ecosystem is larger.
- **Con:** Revisits ADR-0018's "single runner" decision. Worth its
  own ADR when a concrete need justifies the migration cost.

## Follow-ups

- Add the guard's shuffle-order test in a follow-up once
  `unittest` ≥ 3.12's `TestLoader.sortTestMethodsUsing` shuffling
  is wired into `run_tests.py`.
- If a new anti-pattern shows up in review more than twice, promote
  it from review rule to machine rule in a small follow-up PR.

## References

- [ADR-0018](./0018-testing-strategy.md) — Testing strategy (pyramid,
  CI gate).
- [ADR-0023](./0023-coverage-floor-policy.md) — Coverage floor and
  ratchet rules.
- Code: `tests/unittests/quality_guard/test_conventions.py`.
