# ADR-0018: Testing strategy — pyramid, coverage, and CI gating

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** testing, ci, quality

## Context

Before this ADR, pdip's test situation had three problems:

1. **Unit test coverage was thin**: roughly two dozen unit tests
   covering a small slice of the framework. Core abstractions
   (`Dispatcher`, `Pdi`, the pub/sub message broker, the json helpers)
   had no dedicated unit tests.
2. **Integration tests required real databases**: the suite under
   `tests/integrationtests/` targets MSSQL, Oracle, PostgreSQL,
   MySQL, Impala, and SQLite. Only SQLite can run in a vanilla CI
   container; the rest cannot run at all on GitHub-hosted runners
   without infrastructure.
3. **CI did not actually gate on tests**: `run_tests.py` collected
   results but the `if failures: raise` line was commented out, so
   the process always exited `0`. Red tests never broke the build.
4. **Test-only dependencies were implicit**: `dataclasses-json` was
   used by test fixtures but lived only in the `integrator` extra, so
   a clean `pip install -r requirements.txt` produced tests that
   errored out before CI's silent exit masked the problem.

Raising the Python floor for a 3.14 migration (see
[ADR-0019](./0019-python-314-adoption.md)) would be reckless without
addressing these first. A broken safety net doesn't catch you.

## Decision

The testing strategy for pdip is:

### 1. Pyramid

- **Unit tests** (`tests/unittests/`) — the first line of defence.
  Pure Python, no external services, run on every push and PR across
  every supported Python version. Target: every module in `pdip/` has
  at least one unit test covering its public API.
- **Integration tests** (`tests/integrationtests/`) — exercise real
  backends. Run on demand, not on every PR. A backend-specific job
  runs only when infrastructure is available.
- **API smoke tests** (`tests/unittests/api/basic_app*/`) — already
  the strongest end-to-end coverage we have: boot `Pdi`, spin up
  Flask, dispatch a command, hit an endpoint. Keep adding one per
  significant API shape.

### 2. CI gating

- `python run_tests.py` **must** exit non-zero when any test errors
  or fails. This was already fixed by removing the commented
  `raise` and calling `sys.exit(1)` on a non-empty error/failure
  count.
- CI runs the full unit suite on every supported Python version on
  Linux, macOS, and Windows.
- Coverage continues to be collected and uploaded as an artefact
  per job.

### 3. Test dependencies

- Anything imported by a test lives in the dependency list that CI
  installs. At the time of writing that is `requirements.txt`. In
  particular, `dataclasses-json` is a *test* dependency, not
  optional.
- Unit tests must not need a real database, a real Kafka, or a real
  SMTP server. Mock at the boundary or move to
  `tests/integrationtests/`.

### 4. What to test first — priority order

Gaps are closed in this order because these areas have the biggest
downstream blast radius:

1. `pdip.cqrs.dispatcher.Dispatcher` — command / query routing
   convention is load-bearing for the framework.
2. `pdip.base.pdi.Pdi` — the single entry point.
3. `pdip.integrator.pubsub.*` — cross-process eventing, most
   fragile to Python version changes.
4. `pdip.json.base.json_convert` — underpins `@dtoclass`,
   `@request_class`, `@response_class`.
5. `pdip.io.*` and `pdip.utils.*` — stateless helpers, easy wins.

### 5. Coverage policy

- Today's line coverage is the *floor*. New work is expected to hold
  or improve it.
- We do not pick a headline coverage percentage yet. Picking a
  number before the baseline stabilises produces either vanity
  (inflated by trivial tests) or friction (blocking useful PRs
  behind meaningless tests).
- Once the suite is healthy for two release cycles, we pick a
  concrete floor (likely 70–80 % for `pdip/` excluding integration
  adapters) in a follow-up ADR.

### 6. Style

- `unittest` is the default. pdip already uses it consistently and
  we do not add a second runner (`pytest`) unless there's a clear
  reason.
- One test file per module. Name `test_<module>.py`.
- Arrange / Act / Assert, one behaviour per method, self-describing
  method names — `test_dispatcher_raises_when_handler_missing`,
  not `test_dispatcher_1`.

## Consequences

### Positive

- Broken tests break the build. That is the whole point.
- A clean `pip install -r requirements.txt` produces a green test
  suite, so contributors do not chase phantom failures.
- The priority list tells contributors where to spend review effort.

### Negative

- Integration test coverage is still operator-supplied; nothing in
  this ADR makes MSSQL or Oracle run in GitHub Actions. That is a
  separate decision (containerised integration CI, per-adapter
  services, etc.).
- Raising the CI gate will fail the first PR whose tests are actually
  broken. That is the cost of paying down the debt, and it is
  intentional.

### Neutral

- We stay on `unittest`. Contributors familiar with `pytest` may
  find this surprising; we value single-runner uniformity more than
  `pytest`'s ergonomics today.

## Alternatives considered

### Option A — Keep CI non-gating, publish a "known failing" list

- **Pro:** No PR is blocked while the list is worked through.
- **Con:** Red tests rot in place; the list grows, nobody trusts the
  suite.
- **Why rejected:** The status quo that produced this ADR.

### Option B — Rewrite the suite on pytest

- **Pro:** Fixtures, parametrisation, plugin ecosystem.
- **Con:** Every existing test has to move; no user-facing value;
  the underlying gap is coverage, not framework choice.
- **Why rejected:** Wrong fix for the wrong problem.

### Option C — Adopt a minimum coverage % immediately

- **Pro:** One number, easy to gate on.
- **Con:** Teams game the number. A 70 % bar with no unit tests on
  the dispatcher is worse than a 40 % bar that covers it.
- **Why rejected:** Deferred until coverage distribution is
  meaningful.

## Follow-ups

- Open issues tracking unit test coverage for each priority module
  in section 4.
- Decide when the suite is stable enough to pick a coverage floor.
- Document a plan for containerised integration tests (a separate
  ADR when someone picks it up).

## References

- Code: `tests/unittests/`, `tests/integrationtests/`,
  `run_tests.py`.
- CI: `.github/workflows/package-build-and-tests.yml`.
- [ADR-0019](./0019-python-314-adoption.md) — why this ADR landed
  before the 3.14 migration.
