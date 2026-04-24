# ADR-0029: Integration tests run nightly in CI

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** testing, ci, quality, integration
- **Extends:** [ADR-0018](./0018-testing-strategy.md)
- **Relates to:** [ADR-0023](./0023-coverage-floor-policy.md) (the
  `.coveragerc` omit list this ADR fills in for),
  [ADR-0025](./0025-dependabot-auto-merge-policy.md) (Docker image
  bumps reach this workflow via the Dependabot ecosystem added in
  the SHA-pin PR).

## Context

`tests/integrationtests/` has existed in the repository since the
0.7.0 baseline, but nothing in CI has ever run it. Until this ADR
lands, the integration test modules under

```
tests/integrationtests/integrator/integration/sql/{mysql,postgresql,mssql,oracle}/
tests/integrationtests/integrator/connection/{sql,bigdata,inmemory,queue}/…
```

were runnable only by a contributor who:

1. Had Docker installed locally.
2. Knew to start the right `tests/environments/<backend>/docker-compose.yml`.
3. Ran `python -m unittest tests.integrationtests.<path>` by hand.

In practice, nobody does step 2 routinely. The adapter code under
`pdip/integrator/connection/types/{sql,bigdata,webservice,file,inmemory,queue}/`
is therefore covered by **no regression signal** — it is explicitly
excluded from unit-coverage per [ADR-0023 §1](./0023-coverage-floor-policy.md)
and has no CI equivalent. A driver bump (`python-oracledb`,
`confluent-kafka`, `mysql-connector-python`) that breaks the adapter
surface lands to `main` invisibly until a downstream consumer files
a bug.

The gap closed by this ADR.

## Decision

### 1. A new scheduled workflow runs integration tests against real backends

`.github/workflows/integration-tests.yml` boots each backend's
pinned Docker image (the ones maintained under
`tests/environments/<backend>/docker-compose.yml` per the 2026-04-24
image-stabilisation pass) as a GitHub Actions `services:` container
and runs the matching test module against it.

### 2. Triggers

| Trigger | When |
|---|---|
| `schedule: cron: "0 4 * * *"` | Daily at 04:00 UTC. |
| `workflow_dispatch` | Any maintainer can run it on demand from the Actions tab. |
| `pull_request` with narrow `paths:` | **Self-test only** — fires when a PR touches `.github/workflows/integration-tests.yml`, `tests/environments/**`, or `tests/integrationtests/**`. A workflow / fixture edit should not ship as "merge and hope the next nightly is green"; the PR author gets to see it work against real backends before review. |

**Not** triggered on unrelated `push` or `pull_request`. The main CI
workflow (`package-build-and-tests.yml`) stays focused on the fast
unit-test path (< 2 min feedback); running integration tests for
every `pdip/` / test edit would dilute that loop for no commit-level
benefit — driver / image regressions surface on a day-scale, not a
commit-scale.

### 3. Phased backend rollout

The first cut ships with:

- **Postgres 16** — `postgres:16-alpine`.
- **MySQL 8.4** — `mysql:8.4` (LTS).

Deferred to follow-up PRs, each with its own job block:

- **SQL Server 2022** — the image is public but the service health-
  check needs a different pattern (SA password + Developer edition
  accepts EULA at boot).
- **Oracle XE 21c** — boots in ~40 s with the `slim-faststart`
  image, but the pluggable-database lifecycle needs an explicit
  wait-for-ready probe beyond a simple port check.
- **Kafka 7.7.1 + ZooKeeper** — two-service composition; needs a
  topic-create step in the job.
- **Hadoop / Impala bigdata stack** — unmaintained upstream images
  (ADR-0029 follow-up with migration plan first).

Each deferred backend lands as its own PR so a single broken job
does not hold up the others.

### 4. Connection fixture is stable, not parameterised

Integration tests already hard-code credentials (`pdi` / `pdi!123456`
/ `test_pdi` / `localhost:<port>`) to match the docker-compose
fixtures. The workflow `services:` block mirrors those values
exactly. We do **not** introduce a per-environment YAML layer here —
the existing fixture-hardcoded credentials are unambiguous and
rotating them in a future PR is a single search-and-replace.

### 5. No test-matrix explosion

Each backend runs on **one** cell: Python 3.11 / ubuntu-latest /
pinned image version. Integration tests validate the adapter
against the backend, not the interpreter, so a per-Python-version
matrix would be pure noise. When a driver bump needs retesting on a
specific Python, we add a temporary matrix dimension on a follow-up
PR and remove it when done.

### 6. Failure policy

- A nightly failure opens no automatic issue. Maintainers review
  the run via the Actions tab on the day after.
- A `workflow_dispatch` failure is expected to be investigated by
  the maintainer who triggered it.
- Consecutive nightly failures (two or more days) should be flagged
  as a blocker in the next release cut per
  [ADR-0024 §3.1](./0024-release-process.md).

## Consequences

### Positive

- Adapter regressions caught on a day-scale instead of a
  downstream-bug-report-scale.
- The `[integrator]` extras (oracledb, confluent-kafka, pandas,
  mysql-connector-python, pyodbc, psycopg2-binary) have real
  exercise. [ADR-0025](./0025-dependabot-auto-merge-policy.md)
  rule 2 (no auto-merge for integrator drivers) becomes a
  *supervised* human review — nightly result is the supervisor.
- The docker-compose fixtures under `tests/environments/` become
  living infrastructure: if a fixture breaks, the workflow fails
  the next day, and the fix lands before a developer hits it.
- GitHub Actions minutes are free on public repos, so the scheduled
  run is zero-cost.

### Negative

- Two extra workflow runs per day (currently — five once all
  backends land). Even at zero cost, it's queue pressure on free
  runners. Scheduled for 04:00 UTC to dodge peak.
- Flaky image boots (notably Oracle's occasional slow first-start)
  will produce false negatives some mornings. Maintainers must
  distinguish "real" failures from "re-run it and it passes".
- New backends have to be onboarded twice: docker-compose fixture
  **and** a job in this workflow. Small duplication of effort,
  acceptable for the gain.

### Neutral

- The main CI workflow is unchanged — `.coveragerc`'s omit list
  for `pdip/integrator/connection/types/**` stays in place because
  adapter coverage lives in a separate run.

## Alternatives considered

### Option A — Run integration tests on every push

- **Pro:** Zero latency on adapter regressions.
- **Con:** Each integration run is 3–5 min per backend; a full set
  would stretch the 2-min unit feedback loop to 15–20 min. The
  point of [ADR-0018](./0018-testing-strategy.md)'s pyramid is that
  fast tests gate development; breaking that trade-off for an
  edge-case regression-surface is not worth it.
- **Why rejected:** Nightly schedule + on-demand dispatch gives us
  the regression signal without the feedback-loop cost.

### Option B — Run integration tests in a nightly cron external to GitHub Actions

- **Pro:** Avoids GitHub Actions queue-pressure issues.
- **Con:** Adds an external piece of infrastructure to operate
  (cron host, secret management, result publication). For a small
  framework with public repos that get free Actions minutes, the
  cost is all overhead.
- **Why rejected:** Actions is the lowest-friction option.

### Option C — Testcontainers instead of ``services:``

- **Pro:** Same fixture running both in local test runs and in CI —
  the test code itself spins up the container.
- **Con:** Adds a Python dependency (`testcontainers`) and couples
  local-dev tests to a Docker daemon even when the developer's
  workflow is unit-only. The existing docker-compose files serve
  local dev cleanly; `services:` serves CI cleanly; the two don't
  need to be unified.
- **Why rejected:** No new runtime dep for a problem we already have
  two good solutions to.

## Follow-ups

- Add **MSSQL 2022** job (separate PR; needs `ACCEPT_EULA=Y` and a
  service-health probe that works with SA login).
- Add **Oracle XE 21c** job (separate PR; needs a readiness probe
  that waits for the pluggable database, not just the listener).
- Add **Kafka 7.7.1 + ZooKeeper** job (two-service composition,
  topic-create step).
- Consider migrating the Hadoop / Impala bigdata fixtures to
  maintained images before adding their integration-test jobs.
- If failures pile up, introduce a lightweight "open an issue on
  two consecutive red nights" step using
  `JasonEtco/create-an-issue` or similar.

## References

- [`.github/workflows/integration-tests.yml`](../../../.github/workflows/integration-tests.yml)
- [`tests/environments/README.md`](../../../tests/environments/README.md)
- ADR-0018 — Testing strategy (pyramid, deferred integration exec).
- ADR-0023 §1 — Coverage omit list for adapter paths.
- ADR-0024 §3.1 — Release cut requires green CI matrix.
- ADR-0025 — Dependabot auto-merge policy (integrator drivers excluded).
