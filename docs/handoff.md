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
| Pre-commit | `pre-commit install` runs the 7 ADR-0026 / ADR-0027 §5 / ADR-0034 §5 quality rules + blocking flake8 in ~300 ms | [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) |

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
  trio (ADR-0032 / 0033 / 0034 — all Accepted) **plus the three
  foundation slices and five follow-up slices** (factory
  `is_async` flag, `Integrator.integrate` job span, ADR-0034
  quality_guard coverage rule, cross-process `traceparent`
  propagation through `ProcessManager` ↔ `Subprocess`,
  `AsyncIntegrationExecute` ABC + strategy-factory `is_async`
  flag). Pushed for review; not yet merged to `main`. See §4
  "Async / OpenTelemetry / 1.0 cut" for the full landed list and
  what is still queued (asyncpg end-to-end Postgres connector +
  adapter wiring, signature-baseline guard).

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
| Async / OpenTelemetry / 1.0 cut | **All three ADRs Accepted, foundation slices + five follow-ups landed on `claude/handoff-start-continue-OolIR`** ([ADR-0032](governance/adr/0032-hybrid-async-strategy.md) / [ADR-0033](governance/adr/0033-opentelemetry-observability.md) / [ADR-0034](governance/adr/0034-one-zero-readiness-criteria.md); ADR-0007 carries a header note pointing to ADR-0032). **Foundation slices** (one per ADR): (1) ADR-0034 — every documented public package declares `__all__`, `docs/public-api.md` mirrors the contract, drift contract test in `tests/unittests/public_api/`. (2) ADR-0033 — `pdip/observability/` lazy `get_tracer` / `get_meter` (no-op-by-default, `PDIP_OBSERVABILITY_ENABLED` toggle, OTel-missing fallback), the `pdip[observability]` extra, `Dispatcher.dispatch` instrumented with `pdip.cqrs.command` / `pdip.cqrs.query` spans + `pdip.cqrs.handler` attribute. (3) ADR-0032 — `AsyncConnectionSourceAdapter` / `AsyncConnectionTargetAdapter` abstract bases + the `pdip[async]` extra (asyncpg / aiomysql / aioodbc / aiokafka). **Follow-ups landed on top**: (b) `is_async` flag on both `ConnectionSourceAdapterFactory.get_adapter` and `ConnectionTargetAdapterFactory.get_adapter`; the new helper `pdip/integrator/connection/base/_async_extra.py::require_async_extra()` raises a clean `ImportError` with `pdip[async]` install hint when the extra is missing, and the factories raise `NotSupportedFeatureException` for every connection type until the async siblings land. (d-1) `Integrator.integrate` now opens a `pdip.integrator.job` span carrying `pdip.integration.id` / `pdip.integration.name` (safe defaults when the operation fields are `None`); argument-validation errors don't open a span. (e) New quality_guard rule `RuleADR0034NoUndocumentedTopLevelPackage` plus `_ADR0034_INTERNAL_PACKAGES` allowlist (currently just `pdip.base`) — pre-commit suite is now 7 rules. (d-2) Cross-process W3C `traceparent` propagation: `pdip.observability.inject_context` (parent side, returns picklable dict carrier) + `pdip.observability.use_context` (worker side, attaches the extracted context for the duration of `target_method`); `ProcessManager.start_processes` injects the carrier into a fresh kwargs copy under `_pdip_trace_carrier` and `Subprocess.start` pops it before invoking user code. Lazy + no-op when observability disabled or OTel missing — caller dict is never mutated. (c) `AsyncIntegrationExecute` ABC under `pdip/integrator/integration/types/sourcetotarget/strategies/async_/base/`; `IntegrationSourceToTargetExecuteStrategyFactory.get(process_count, is_async=False)` learns the new flag — `is_async=True` short-circuits with `NotSupportedFeatureException` pointing at ADR-0032 follow-up until a concrete async strategy lands. | **Still queued for follow-up sessions** — both fundamentally outside one tractable unit-test-driven slice: (a) async Postgres sibling **end-to-end** via `asyncpg` under `pdip/integrator/connection/types/sql/connectors/postgresql/` + `AsyncSqlSourceAdapter` / `AsyncSqlTargetAdapter` wiring, gated by integration tests against a real Postgres instance; this also unlocks unblocking the `is_async=True` paths on the adapter factories so they return real adapters instead of `NotSupportedFeatureException`. (e-2) Signature-baseline guard for ADR-0034 §5 — needs its own design ADR to pick the baseline source (PyPI sdist / git-tag introspection / checked-in snapshot) and the diff algorithm; the `signature guard` row in ADR-0034 §5 already records this. **Optional next steps that are tractable in unit tests**: deeper ADR-0033 instrumentation — `pdip.integrator.source.read` / `pdip.integrator.target.write` spans at the adapter call sites inside the strategy modules (`singleprocess/`, `parallelthread/` — note `parallelthread/` is currently excluded from unit coverage by `.coveragerc` so plan accordingly). TDD focus still mandated — ADR-0027 diff-cover 100 % gate + ADR-0026 / ADR-0034 quality_guard rules (now 7 rules). |

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
(after two more follow-up slices landed: cross-process W3C
`traceparent` propagation via the new
`pdip.observability.inject_context` / `use_context` helpers wired
through `ProcessManager.start_processes` and `Subprocess.start`;
and `AsyncIntegrationExecute` ABC under
`strategies/async_/base/` + an `is_async` flag on
`IntegrationSourceToTargetExecuteStrategyFactory.get` that raises
`NotSupportedFeatureException` until a concrete async strategy
lands. Branch now carries 8 first-implementation slices on top of
the three Accepted ADRs; sits at 100 % unit coverage on the
canonical `run_tests.py` cell (731 tests) with all 7 quality_guard
rules green. Remaining queued work — asyncpg end-to-end Postgres
sibling + signature-baseline guard ADR — recorded in §4
Async/OTel/1.0 row.). When you change anything above, bump this
line with the date and the branch name so the next reader knows
the freshness window at a glance.*
