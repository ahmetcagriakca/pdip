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
| Pre-commit | `pre-commit install` runs the 10 ADR-0026 / ADR-0027 §5 / ADR-0034 §5 / ADR-0035 §3 / ADR-0036 §2 quality rules + blocking flake8 in ~300 ms | [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) |

## 2. Open PRs

No tracked open PRs as of 2026-04-26 (other than this branch's
PR itself, which closes ADR-0030 Stage 3 prerequisite (b) by
filling in real test bodies for the Apache Impala fixture and
refreshes this handoff alongside it). The Async / OTel / 1.0 cut work-stream
landed on `main` across **#116** (foundation + first five follow-ups),
**#117** (post-merge handoff refresh), **#118** (asyncpg Postgres
end-to-end + ADR-0035 signature-snapshot guard), **#119**
(post-#118 handoff refresh), **#120** (async MySQL/MSSQL/Oracle
skeletons + Postgres `clear_data` end-to-end +
`SingleProcessIntegrationExecute` adapter-call-site spans +
ADR-0036 Proposed), **#121** (post-#120 handoff refresh),
**#122** — the finishing slice that lands `pdip.__version__` +
ADR-0036 Accepted with both quality_guard rules + Postgres
`write_data` / `do_target_operation` / iterator / paging
end-to-end + `parallelthread/` adapter-call-site spans + the
integration-tests CI nightly installing `pdip[async]` and running
the per-backend async smoke suites — **#123** (post-#122 handoff
refresh), **#124** (bookkeeping refresh adding #123 to the chain
and `claude/handoff-post-122-refresh-OolIR` to §3's artifact
list), and **#125** — extends the async adapter chain from
Postgres-only to all four backends (a-3) via a new
`async_sql_dialect` helper, brings each backend's integration
suite from 2 connector smoke tests to the full 8-test adapter
shape, **verifies the per-backend async smoke jobs run green
end-to-end on the integration-tests workflow (a-5 DONE)** and
fixes a chain of pre-existing bugs in the sync connectors and
smoke setUps that the green-run verification surfaced (Driver-18
hardcoded `AsyncMssqlConnector`, bare-`mysql://` SQLAlchemy URL,
bare-path Oracle URL → `?service_name=` for PDB lookup, MSSQL /
Oracle smoke + sync setUps aligned to workflow credentials,
MySQL `test_check_schema_and_tables` skipping system schemas
that need `PROCESS`), **#126** (post-#125 handoff refresh),
**#127** (bookkeeping refresh adding #126 to the chain and
`claude/handoff-post-125-refresh-OolIR` to §3's artifact list),
and **#128** (`parallelold/` adapter-call-site spans — last
foundation item (a-4) on the Async / OTel / 1.0 work-stream;
+8 unit tests; 781/781 green).
See §4 for the full breakdown. Earlier
Dependabot bumps (#61 pyodbc 5.3.0, #63 markupsafe 3.0.3, #64
oracledb upper-bound to allow 3.x) merged after a surface-area
audit against the adapter call sites — see commits `cdd1bb5`,
`ead2013`, `a799d7d`.

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

- **Active:** `claude/impala-test-bodies-Iz4XK` — fills in real
  test bodies for the Apache Impala fixture
  (ADR-0030 Stage 3 prerequisite (b)) and refreshes this handoff.
  PR not yet open at refresh time. Post-merge artifacts safe to
  ignore:
  `claude/handoff-start-continue-OolIR` (#116),
  `claude/handoff-post-merge-OolIR` (#117),
  `claude/handoff-asyncpg-sigguard-OolIR` (#118),
  `claude/handoff-post-118-refresh-OolIR` (#119),
  `claude/handoff-async-backends-spans-OolIR` (#120),
  `claude/handoff-post-120-refresh-OolIR` (#121),
  `claude/handoff-finish-stream-OolIR` (#122),
  `claude/handoff-post-122-refresh-OolIR` (#123),
  `claude/handoff-post-123-refresh-OolIR` (#124),
  `claude/review-handoff-async-50eob` (#125),
  `claude/handoff-post-125-refresh-OolIR` (#126),
  `claude/handoff-post-126-refresh-OolIR` (#127),
  `claude/handoff-state-management-p13Rm` (#128), and the current
  branch once its PR squash-merges.

If you find a `claude/*` branch not listed here and not associated with an
open PR, it is almost certainly stale — confirm with `git log
origin/main..origin/<branch>` before deleting.

## 4. Deferred decisions

Each row is something we *intentionally did not do*. Pick one up with an
ADR if the answer changed.

| Topic | Status | Pointer |
|---|---|---|
| Kafka nightly integration job | Smoke-test scaffold for `KafkaConnector` lives at `tests/integrationtests/integrator/connection/queue/kafka/` and runs locally against `tests/environments/kafka/docker-compose.yml`. The matching nightly CI job did *not* land — four image / config combinations failed (cp-kafka + cp-zookeeper, apache/kafka 3.7 KRaft, bitnami/kafka 3.7 KRaft, plus a debug log-dump variant) and the Actions logs are auth-walled to non-collaborators. | A maintainer with collaborator access reads the actual job log to identify the broker-exit cause, then opens one targeted fix PR adding the `kafka:` job to `.github/workflows/integration-tests.yml`. |
| Hadoop / Impala fixtures + bigdata nightly | [ADR-0030](governance/adr/0030-hadoop-impala-fixture-migration.md) (Status: Proposed). Stage 1 fully landed: mechanical part in #110 (deleted `tests/environments/hadoop/`), substantive part in #114 (translated upstream `apache/impala/docker/quickstart.yml` into a 4-service fixture under `tests/environments/bigdata/impala/` + vendored `quickstart_conf/hive-site.xml`). **Stage 3 prerequisite (b) DONE on this branch** — both `tests/integrationtests/integrator/integration/bigdata/impala/test_integration_{single_process,limit_off}.py` now carry real test bodies modelled on `tests/integrationtests/integrator/integration/sql/postgresql/test_integrator.py`, routing through a new `tests/integrationtests/integrator/integration/bigdata/utils/TestBigDataUtils` helper (mirrors `TestSqlUtils` for the bigdata adapter), targeting the fixture's `localhost:21050` HS2 endpoint with `MechanismTypes.NoAuthentication` + the `default` Hive database. Both files import-load cleanly under the current pdip API (`Integrator.integrate`, `BigDataProvider`, `ConnectionBigDataBase`, `ConnectionServer`, `ConnectionBasicAuthentication`, `ConnectorTypes.Impala`); the unit suite stays at 781 / 781 green with no regression. | One open prerequisite remains before Stage 3 (`impala:` nightly job) lands: (a) maintainer with Docker access boots the new fixture and confirms `localhost:21050` accepts pyodbc — fixture has not been locally validated, and the new test bodies have not been live-validated either. |
| Async / OpenTelemetry / 1.0 cut | **All five ADRs Accepted (0032 / 0033 / 0034 / 0035 / 0036); the work-stream is contractually complete on `main` AND foundation-complete across every execution strategy**. ADR-0034 §5 enforcement is now 4 layers, all shipped: drift contract test, `RuleADR0034NoUndocumentedTopLevelPackage` coverage rule, `RuleADR0035PublicApiSignatureSnapshotMatches` signature guard, and the new pair `RuleADR0036DeprecationWarningHasManifestEntry` + `RuleADR0036RemovalRespectsDeprecationCycle` deprecation-cycle guard reading `docs/public-api-deprecations.json`. `pdip.__version__` is exported as the single source of truth for the runtime version (read by the removal-cycle rule). `pdip.observability` exports `get_tracer` / `get_meter` / `inject_context` / `use_context`; `pdip[observability]` and `pdip[async]` extras live in `setup.py`; `Dispatcher.dispatch`, `Integrator.integrate`, `SingleProcessIntegrationExecute`, `parallelthread/operation/{source,target}`, AND now **`parallelold/base/parallel_integration_execute.py`** emit `pdip.cqrs.{command,query}` / `pdip.integrator.job` / `pdip.integrator.source.read` / `pdip.integrator.target.write` spans with their documented attributes via the shared `strategies/base/span_helpers.py`; the async Sql chain dispatches via `_connector_for` to `AsyncPostgresqlConnector` / `AsyncMysqlConnector` / `AsyncMssqlConnector` / `AsyncOracleConnector` (lazy driver imports throughout); `AsyncSqlConnector` ABC has `connect`/`disconnect`/`fetch_count`/`execute`/`fetch_all`/`executemany`; **`AsyncSqlTargetAdapter` and `AsyncSqlSourceAdapter` are fully wired for ALL FOUR backends** — `clear_data` (TRUNCATE), `write_data` (executemany INSERT with column inference + dialect-specific placeholder ladder), `do_target_operation` (truncate-when-flag-set), `get_iterator` (in-memory chunked batches), `get_source_data_with_paging` (LIMIT/OFFSET on Postgres + MySQL, ANSI OFFSET/FETCH NEXT on MSSQL + Oracle), `get_source_data_count`. The dialect helper at `pdip/integrator/connection/types/sql/base/async_sql_dialect.py` centralises identifier quoting, placeholder rendering, paging-clause shape, and TRUNCATE wording per backend; both adapters route through `async_dialect_for(config)` instead of hard-coding Postgres syntax. Cross-process W3C `traceparent` propagation through `ProcessManager` ↔ `Subprocess`. Integration-tests CI nightly installs `pdip[integrator,async]` and runs per-backend `connection/sql/<backend>/test_async_connection.py` smoke jobs alongside the existing sync integration suites — every backend exercises the full 8-test adapter shape (connector smoke + 6 adapter methods) instead of just connect/fetch_count, and the workflow is **verified green end-to-end** for all four backends (Postgres 16, MySQL 8.4, SQL Server 2022, Oracle XE 21c). Pre-commit suite is 10 rules. | **What is left on this work-stream**: nothing on the foundation. (a-4) **DONE — `parallelold/base/parallel_integration_execute.py` now wraps `start_source_data_operation`'s `get_source_data_count` in `pdip.integrator.source.read`, `start_execute_integration_with_source_data`'s `write_data` in `pdip.integrator.target.write`, and `start_execute_integration_with_paging`'s read+write pair in source.read+target.write spans with the documented `pdip.connection.{type,driver}` / `pdip.batch.size` / `pdip.rows.written` attributes via `strategies/base/span_helpers.py`. Pinned by 8 new unit tests under `tests/unittests/integrator/integration/parallelold/test_parallel_integration_execute_spans.py`.** (a-5 verification) DONE on PR #125. With (a-4) landed, the Async / OTel / 1.0-readiness work is **foundation-complete across every execution strategy** (single-process, parallel-thread, parallel-process/old, async). TDD focus still mandated — ADR-0027 diff-cover 100 % gate + ADR-0026 / ADR-0034 / ADR-0035 / ADR-0036 quality_guard rules (10 rules). |

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

*Last updated 2026-04-26 on `claude/impala-test-bodies-Iz4XK`
(closes ADR-0030 Stage 3 prerequisite (b) — the
`tests/integrationtests/integrator/integration/bigdata/impala/test_integration_*.py`
files were 170 lines of commented-out stubs; this branch fills
in real test bodies modelled on the `postgresql/test_integrator.py`
shape and refreshes this handoff). `main` is at `467b3b5` (#128
landed, so the `parallelold/` adapter-call-site spans (a-4) are
on `main`; the Async / OTel / 1.0 readiness work-stream remains
**foundation-complete across every execution strategy** with
five Accepted ADRs (0032 / 0033 / 0034 / 0035 / 0036)).
Concretely on this branch:
`tests/integrationtests/integrator/integration/bigdata/impala/test_integration_single_process.py`
and `.../test_integration_limit_off.py` now hold real
`TestImpalaIntegration{SingleProcess,LimitOff}` cases that
target the Apache Impala 4.5.0 fixture's HS2 endpoint at
`localhost:21050` with `MechanismTypes.NoAuthentication` + the
default Hive `default` database (the fixture is auth-less by
construction). A new
`tests/integrationtests/integrator/integration/bigdata/utils/`
package introduces `TestBigDataUtils` — the bigdata mirror of
`TestSqlUtils` — routing through `BigDataProvider` /
`BigDataContext` for `prepare_test_data_with_info` +
`get_operation`. Both test files import-load cleanly under the
current pdip API
(`Integrator.integrate`, `BigDataProvider`, `ConnectionBigDataBase`,
`ConnectionServer`, `ConnectorTypes.Impala`); the unit suite stays
at 781 / 781 green. Public surface unchanged (no `pdip/` source
edits, only `tests/integrationtests/`). ADR-0034 §5 enforcement
unchanged (4 layers: drift / coverage / signature /
deprecation-cycle); 10 quality_guard rules green.
**Remaining queued work on §4 Hadoop/Impala row:** prerequisite
(a) — maintainer with Docker access boots the fixture once and
confirms `localhost:21050` accepts pyodbc + the new test bodies
pass against the live cluster. Once (a) is done, ADR-0030 Stage 3
(`impala:` job in the integration-tests workflow) is unblocked.
**Other §4 deferred items unchanged:** Kafka nightly CI job is
still the only foundation gap left for 1.0 readiness across the
adapter matrix. When you change anything above, bump this line
with the date and the branch name so the next reader knows the
freshness window at a glance.*
