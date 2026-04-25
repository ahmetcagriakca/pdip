# Handoff

> **Audience:** the next contributor (or future-you) opening this repo cold.
> Read this before opening a session — the goal is to get you to a useful
> first action in under 60 seconds without rummaging through chat history.
>
> **Cadence:** update at the same time you cut a release, open or close a
> tracked PR, or accept an ADR with deferred follow-ups. Stale handoffs
> are worse than no handoff — if a row here disagrees with `main`, `main`
> wins, fix the row.

## 1. Live state of `main`

| Thing | Value | Source of truth |
|---|---|---|
| Latest release | **v0.8.0** (2026-04-24) | [CHANGELOG.md](../CHANGELOG.md), [GitHub release](https://github.com/ahmetcagriakca/pdip/releases/tag/v0.8.0) |
| Unit coverage | **100 %**, `fail_under = 100` enforced | [`.coveragerc`](../.coveragerc), [ADR-0023](governance/adr/0023-coverage-floor-policy.md) |
| Diff coverage | **100 %** of changed `pdip/` lines vs `main` | [ADR-0027](governance/adr/0027-tdd-with-diff-coverage.md) |
| Python floor | **3.10** (3.9 EOL, ADR-0028 supersedes ADR-0020) | [ADR-0028](governance/adr/0028-raise-python-floor-to-3-10.md) |
| Unit-test CI matrix | Python 3.10 / 3.11 / 3.12 / 3.13 / 3.14 × macOS / Windows / Ubuntu | [`.github/workflows/package-build-and-tests.yml`](../.github/workflows/package-build-and-tests.yml) |
| Integration CI | Nightly 04:00 UTC + `workflow_dispatch` + workflow self-test PR trigger; runs Postgres 16, MySQL 8.4, Oracle XE 21c, **SQL Server 2022** | [`.github/workflows/integration-tests.yml`](../.github/workflows/integration-tests.yml), [ADR-0029](governance/adr/0029-integration-tests-in-ci.md) |
| Pre-commit | `pre-commit install` runs the 6 ADR-0026/0027 §5 quality rules + blocking flake8 in ~300 ms | [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) |

## 2. Open PRs

No tracked open PRs as of 2026-04-25. The three Dependabot bumps that were
previously open here (#61 pyodbc 5.3.0, #63 markupsafe 3.0.3, #64 oracledb
upper-bound to allow 3.x) have all merged after a surface-area audit
against the adapter call sites — see commits `cdd1bb5`, `ead2013`,
`a799d7d`.

When new PRs come in, list them here with the same four columns
(`#`, `What`, `Next action`, `Why deferred`) so the next reader can act
without re-doing the analysis. If `gh pr list --state open` returns
nothing for this repo, write a one-line "none" note like this one and
move on — an empty section is fine, a missing section invites guesswork.

## 3. Branches

The active branch for the next handoff iteration is documented at the bottom
of this file. Most `claude/*` branches on the remote are post-merge
artifacts from squash-merged PRs — safe to ignore unless a name below is
listed. **Reserved (not yet pushed):**

- `claude/handoff-start-continue-OolIR` — Async / OTel / 1.0 ADR
  trio (ADR-0032 / 0033 / 0034 — all three Accepted) **plus the
  three foundation first-implementation slices** (ADR-0034 public-
  API audit, ADR-0033 observability lazy helpers + Dispatcher
  spans, ADR-0032 async adapter bases + `pdip[async]` extra).
  Pushed for review; not yet merged to `main`. See §4 "Async /
  OpenTelemetry / 1.0 cut" for what landed and the queued follow-up
  PRs (asyncpg connector, factory `is_async` flag, async strategy,
  Integrator/adapter OTel instrumentation, cross-process trace
  context, ADR-0034 quality_guard rule expansion).

If you find a `claude/*` branch not listed here and not associated with an
open PR, it is almost certainly stale — confirm with `git log
origin/main..origin/<branch>` before deleting.

## 4. Deferred decisions

Each row is something we *intentionally did not do*. Pick one up with an
ADR if the answer changed.

| Topic | Status | Pointer |
|---|---|---|
| Kafka nightly integration job | Smoke-test scaffold for `KafkaConnector` lives at `tests/integrationtests/integrator/connection/queue/kafka/` and runs locally against `tests/environments/kafka/docker-compose.yml`. The matching nightly CI job did *not* land — four image / config combinations failed (cp-kafka + cp-zookeeper, apache/kafka 3.7 KRaft, bitnami/kafka 3.7 KRaft, plus a debug log-dump variant) and the Actions logs are auth-walled to non-collaborators. | A maintainer with collaborator access reads the actual job log to identify the broker-exit cause, then opens one targeted fix PR adding the `kafka:` job to `.github/workflows/integration-tests.yml`. |
| Hadoop / Impala fixtures + bigdata nightly | [ADR-0030](governance/adr/0030-hadoop-impala-fixture-migration.md) (Status: Proposed). Stage 1 fully landed: mechanical part in #110 (deleted `tests/environments/hadoop/`), substantive part in #114 (translated upstream `apache/impala/docker/quickstart.yml` into a 4-service fixture under `tests/environments/bigdata/impala/` + vendored `quickstart_conf/hive-site.xml`). | Two open prerequisites before Stage 3 (`impala:` nightly job) lands: (a) maintainer with Docker access boots the new fixture and confirms `localhost:21050` accepts pyodbc — fixture has not been locally validated; (b) somebody uncomments / rewrites the test bodies under `tests/integrationtests/integrator/integration/bigdata/impala/test_integration_*.py`, which today are stub files (every line is `# from unittest …`). |
| Async / OpenTelemetry / 1.0 cut | **All three ADRs Accepted, foundation slices landed on `claude/handoff-start-continue-OolIR`** ([ADR-0032](governance/adr/0032-hybrid-async-strategy.md) hybrid async / [ADR-0033](governance/adr/0033-opentelemetry-observability.md) OTel / [ADR-0034](governance/adr/0034-one-zero-readiness-criteria.md) 1.0 readiness; ADR-0007 carries a header note pointing to ADR-0032). What landed in this session: (1) **ADR-0034 slice 1** — every documented public package declares `__all__`, `docs/public-api.md` mirrors the contract, and `tests/unittests/public_api/test_public_api_contract.py` machine-checks drift. (2) **ADR-0033 slice 2** — `pdip/observability/` lazy `get_tracer` / `get_meter` (no-op-by-default, `PDIP_OBSERVABILITY_ENABLED` toggle, OTel-missing fallback), the `pdip[observability]` extra, and `pdip/cqrs/dispatcher.py` instrumented with `pdip.cqrs.command` / `pdip.cqrs.query` spans carrying the `pdip.cqrs.handler` attribute. (3) **ADR-0032 slice 3 (foundation only)** — `AsyncConnectionSourceAdapter` / `AsyncConnectionTargetAdapter` abstract bases + the `pdip[async]` extra (asyncpg / aiomysql / aioodbc / aiokafka). All three slices ship at 100 % unit coverage on the canonical `run_tests.py` cell with ADR-0026 quality_guard green. | **Slice 3 deliberately did NOT include** the asyncpg Postgres connector, the `is_async` flag on `ConnectionSourceAdapterFactory`, or registration of the async strategy in `IntegrationSourceToTargetExecuteStrategyFactory` — those are integration-test territory (real Postgres, asyncpg dependency) and outside one tractable unit-test-driven slice. **Queued follow-ups** (each one a separate PR): (a) async Postgres sibling end-to-end via `asyncpg` under `pdip/integrator/connection/types/sql/connectors/postgresql/`, gated by integration tests; (b) `is_async` flag on the source/target adapter factories with clean `ImportError` when the `pdip[async]` extra is missing; (c) `AsyncIntegrationExecute` strategy under `pdip/integrator/integration/types/sourcetotarget/strategies/async_/` and its registration in the strategy factory; (d) ADR-0033 follow-ups — instrument `Integrator.run`, the source/target adapter call sites, then cross-process W3C `traceparent` propagation through `Subprocess`; (e) ADR-0034 follow-ups — broaden the public-API contract test into a full quality_guard rule that catches signature breaks against the previous minor and add a release-PR template item per §4. TDD focus still mandated — ADR-0027 diff-cover 100 % gate + ADR-0026 quality_guard rules. |

## 5. Read this first

Order matters — the first three rows give you the framing you need for the
rest.

1. [`docs/governance/README.md`](governance/README.md) — how decisions are
   made (MADR + policies).
2. [`docs/governance/adr/README.md`](governance/adr/README.md) — index of
   all ADRs and their status.
3. [`CHANGELOG.md`](../CHANGELOG.md) — `[Unreleased]` shows what is in
   flight on `main` since v0.8.0.
4. [`CONTRIBUTING.md`](../CONTRIBUTING.md) — workflow expectations, ties
   into ADR-0026 and ADR-0027.
5. [`docs/governance/policies/`](governance/policies/) — coding,
   branching, releasing rules that apply day-to-day.
6. Latest release notes:
   [v0.8.0](https://github.com/ahmetcagriakca/pdip/releases/tag/v0.8.0).

---

*Last updated 2026-04-25 on `claude/handoff-start-continue-OolIR`
(after the three Async / OTel / 1.0-cut ADRs were Accepted and
their foundation first-implementation slices landed: ADR-0034
public-API audit + drift contract test, ADR-0033 lazy
observability helpers + Dispatcher spans + `pdip[observability]`
extra, ADR-0032 async adapter bases + `pdip[async]` extra. ADR-0007
carries a header note pointing to ADR-0032. Branch sits at 100 %
unit coverage with ADR-0026 quality_guard green; queued follow-ups
recorded in §4 Async/OTel/1.0 row.). When you change anything
above, bump this line with the date and the branch name so the
next reader knows the freshness window at a glance.*
