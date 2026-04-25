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

No tracked open PRs as of 2026-04-25. The Async / OTel / 1.0 cut
work-stream landed on `main` across **#116** (foundation + first
five follow-ups), **#117** (post-merge handoff refresh), **#118**
(asyncpg Postgres end-to-end + ADR-0035 signature-snapshot guard),
**#119** (post-#118 handoff refresh), **#120** (async
MySQL/MSSQL/Oracle skeletons + Postgres `clear_data` end-to-end +
`SingleProcessIntegrationExecute` adapter-call-site spans + ADR-0036
Proposed), **#121** (post-#120 handoff refresh), and **#122** —
the finishing slice that lands `pdip.__version__` + ADR-0036
Accepted with both quality_guard rules + Postgres `write_data` /
`do_target_operation` / iterator / paging end-to-end +
`parallelthread/` adapter-call-site spans + the integration-tests
CI nightly installing `pdip[async]` and running the per-backend
async smoke suites. See §4 for the full breakdown. Earlier
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

- No active reserved branches at the moment. Post-merge
  artifacts safe to ignore:
  `claude/handoff-start-continue-OolIR` (#116),
  `claude/handoff-post-merge-OolIR` (#117),
  `claude/handoff-asyncpg-sigguard-OolIR` (#118),
  `claude/handoff-post-118-refresh-OolIR` (#119),
  `claude/handoff-async-backends-spans-OolIR` (#120),
  `claude/handoff-post-120-refresh-OolIR` (#121),
  `claude/handoff-finish-stream-OolIR` (#122), and the current
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
| Hadoop / Impala fixtures + bigdata nightly | [ADR-0030](governance/adr/0030-hadoop-impala-fixture-migration.md) (Status: Proposed). Stage 1 fully landed: mechanical part in #110 (deleted `tests/environments/hadoop/`), substantive part in #114 (translated upstream `apache/impala/docker/quickstart.yml` into a 4-service fixture under `tests/environments/bigdata/impala/` + vendored `quickstart_conf/hive-site.xml`). | Two open prerequisites before Stage 3 (`impala:` nightly job) lands: (a) maintainer with Docker access boots the new fixture and confirms `localhost:21050` accepts pyodbc — fixture has not been locally validated; (b) somebody uncomments / rewrites the test bodies under `tests/integrationtests/integrator/integration/bigdata/impala/test_integration_*.py`, which today are stub files (every line is `# from unittest …`). |
| Async / OpenTelemetry / 1.0 cut | **All five ADRs Accepted (0032 / 0033 / 0034 / 0035 / 0036); the work-stream is contractually complete on `main`**. ADR-0034 §5 enforcement is now 4 layers, all shipped: drift contract test, `RuleADR0034NoUndocumentedTopLevelPackage` coverage rule, `RuleADR0035PublicApiSignatureSnapshotMatches` signature guard, and the new pair `RuleADR0036DeprecationWarningHasManifestEntry` + `RuleADR0036RemovalRespectsDeprecationCycle` deprecation-cycle guard reading `docs/public-api-deprecations.json`. `pdip.__version__` is exported as the single source of truth for the runtime version (read by the removal-cycle rule). `pdip.observability` exports `get_tracer` / `get_meter` / `inject_context` / `use_context`; `pdip[observability]` and `pdip[async]` extras live in `setup.py`; `Dispatcher.dispatch`, `Integrator.integrate`, `SingleProcessIntegrationExecute`, AND `parallelthread/operation/{source,target}` now emit `pdip.cqrs.{command,query}` / `pdip.integrator.job` / `pdip.integrator.source.read` / `pdip.integrator.target.write` spans with their documented attributes via the shared `strategies/base/span_helpers.py`; the async Sql chain dispatches via `_connector_for` to `AsyncPostgresqlConnector` / `AsyncMysqlConnector` / `AsyncMssqlConnector` / `AsyncOracleConnector` (lazy driver imports throughout); `AsyncSqlConnector` ABC has `connect`/`disconnect`/`fetch_count`/`execute`/`fetch_all`/`executemany`; **`AsyncSqlTargetAdapter` is fully wired for Postgres — `clear_data` (TRUNCATE), `write_data` (executemany INSERT with column inference), `do_target_operation` (truncate-when-flag-set)** and `AsyncSqlSourceAdapter` likewise — `get_iterator` (in-memory chunked batches), `get_source_data_with_paging` (LIMIT/OFFSET), `get_source_data_count`. Cross-process W3C `traceparent` propagation through `ProcessManager` ↔ `Subprocess`. Integration-tests CI nightly now installs `pdip[integrator,async]` and runs per-backend `connection/sql/<backend>/test_async_connection.py` smoke jobs alongside the existing sync integration suites. Pre-commit suite is 10 rules. | **What is left on this work-stream**: (a-3 remaining) async iterator/paging + write_data/do_target_operation for the **non-Postgres** backends (MySQL/MSSQL/Oracle) — the dialect-specific placeholder ladder + per-driver bulk-insert semantics each warrant their own slice; current behaviour is the Postgres path lights up real, the others go through `_connector_for` and run against their respective async-extra clients but only the connect/fetch_count/execute primitives are wired today. (a-4 remaining) Span instrumentation of `parallelold/` (multiprocessing) strategy — same span vocabulary already extracted into `strategies/base/span_helpers.py`. (a-5 verification) Confirm the per-backend async smoke jobs go green on the integration-tests nightly once the workflow actually runs (the YAML change is shipped; the green run is the verification). The Async / OTel / 1.0-readiness work is **architecturally complete** — what remains is breadth (more backends) and the parallelold multiprocessing path. TDD focus still mandated — ADR-0027 diff-cover 100 % gate + ADR-0026 / ADR-0034 / ADR-0035 / ADR-0036 quality_guard rules (now 10 rules). |

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

*Last updated 2026-04-25 on `claude/handoff-post-122-refresh-OolIR`
(post-merge refresh after #122 squash-merged the finishing slice
of the Async / OTel / 1.0 readiness work-stream to `main`).
`main` is at `582f35d`; the work-stream is now contractually +
architecturally complete with five Accepted ADRs (0032 / 0033 /
0034 / 0035 / 0036), a public surface that includes
`pdip.__version__` + `pdip.observability` + the async adapter
chain wired Postgres-end-to-end through both connection
factories, ADR-0034 §5 enforcement complete in **four layers,
all shipped** (drift / coverage / signature / deprecation-cycle),
the `singleprocess/` AND `parallelthread/` strategies emitting
the documented adapter-call-site spans via the shared
`strategies/base/span_helpers.py`, and the integration-tests CI
nightly installing `pdip[integrator,async]` + running the
per-backend async smoke suites alongside the sync integration
suites. 100 % unit coverage on the canonical `run_tests.py`
cell (747 tests); 10 quality_guard rules green. Remaining queued
work — the non-Postgres async write_data/iterator
implementations and the `parallelold/` multiprocessing strategy
spans — is breadth, not foundation. Recorded in §4
Async/OTel/1.0 row. When you change anything above, bump this
line with the date and the branch name so the next reader knows
the freshness window at a glance.*
