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
| Pre-commit | `pre-commit install` runs the 8 ADR-0026 / ADR-0027 §5 / ADR-0034 §5 / ADR-0035 §3 quality rules + blocking flake8 in ~300 ms | [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) |

## 2. Open PRs

No tracked open PRs as of 2026-04-25. The Async / OTel / 1.0 cut work
landed on `main` across **#116** (foundation + first five follow-ups,
squash-merged), **#117** (post-merge handoff refresh), and the
queued-follow-up PR that lands the asyncpg Postgres end-to-end
sibling + ADR-0035 signature-snapshot guard. See §4 for the full
list of what came in. Earlier Dependabot bumps (#61 pyodbc 5.3.0,
#63 markupsafe 3.0.3, #64 oracledb upper-bound to allow 3.x) merged
after a surface-area audit against the adapter call sites — see
commits `cdd1bb5`, `ead2013`, `a799d7d`.

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
  `claude/handoff-post-118-refresh-OolIR` (#119), and the
  current branch once its PR squash-merges.

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
| Async / OpenTelemetry / 1.0 cut | **All ADRs Accepted (0032 / 0033 / 0034 / 0035), ADR-0036 Proposed; foundation + ten follow-ups landed on `main`**. What is now on `main`: every documented public package declares `__all__` mirrored in `docs/public-api.md`; `pdip.observability` exports `get_tracer` / `get_meter` / `inject_context` / `use_context` (lazy no-op-by-default, `PDIP_OBSERVABILITY_ENABLED` toggle, OTel-missing fallback); `pdip[observability]` and `pdip[async]` extras live in `setup.py`; `Dispatcher.dispatch`, `Integrator.integrate`, AND now `SingleProcessIntegrationExecute.execute` emit `pdip.cqrs.{command,query}` / `pdip.integrator.job` / `pdip.integrator.source.read` / `pdip.integrator.target.write` spans with their documented attributes (per-page `pdip.rows.written`, `pdip.batch.size`, etc.); `AsyncConnectionSourceAdapter` / `AsyncConnectionTargetAdapter` abstract bases + the `is_async` flag on the connection factories route to real async adapters for `ConnectionTypes.Sql`; the async Sql adapter chain dispatches via `_connector_for` to `AsyncPostgresqlConnector` (asyncpg) **plus the new `AsyncMysqlConnector` (aiomysql) / `AsyncMssqlConnector` (aioodbc) / `AsyncOracleConnector` (oracledb async)** — each with lazy import of its driver so module import never depends on the `pdip[async]` extra; `AsyncSqlConnector` ABC gained `execute(query)`, with a Postgres implementation that powers `AsyncSqlTargetAdapter.clear_data` (`TRUNCATE TABLE`) end-to-end; cross-process W3C `traceparent` propagation through `ProcessManager` ↔ `Subprocess`; ADR-0034 §5 enforcement complete in three layers (drift / coverage / signature) — `RuleADR0035PublicApiSignatureSnapshotMatches` against `docs/public-api-signatures.json` (regen helper at `scripts/regenerate_public_api_signatures.py`). Pre-commit suite is 8 rules. | **What is left on this work-stream**: (a-3 remaining) async iterator + paging support on `AsyncSqlSourceAdapter`; async `write_data` / `do_target_operation` on `AsyncSqlTargetAdapter` (currently `NotImplementedError` stubs with ADR-0032 pointers; `clear_data` is now Postgres-end-to-end). (a-4 remaining) Span instrumentation of `parallelthread/` and `parallelold/` strategies (both excluded from unit coverage by `.coveragerc` — same span vocabulary, lifted from `singleprocess/`). (a-5) Integration tests for MySQL / MSSQL / Oracle async smokes against their Docker fixtures (smoke scaffolds shipped, gated by their respective extras). (e-3) **ADR-0036 Proposed** — picks a checked-in `docs/public-api-deprecations.json` manifest as the baseline, plus two new quality_guard rules (`RuleADR0036DeprecationWarningHasManifestEntry` + `RuleADR0036RemovalRespectsDeprecationCycle`); implementation is the Follow-ups list, not yet shipped. TDD focus still mandated — ADR-0027 diff-cover 100 % gate + ADR-0026 / ADR-0034 / ADR-0035 quality_guard rules. |

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

*Last updated 2026-04-25 on `claude/handoff-async-backends-spans-OolIR`
(after the post-#119 follow-ups landed: (a-2) async MySQL /
MSSQL / Oracle connector skeletons + `_connector_for` dispatch +
per-backend integration smoke scaffolds; (a-3 partial)
`AsyncSqlConnector.execute` + `AsyncPostgresqlConnector.execute`
+ `AsyncSqlTargetAdapter.clear_data` end-to-end for Postgres
(`TRUNCATE TABLE`); (a-4) `pdip.integrator.source.read` /
`pdip.integrator.target.write` spans in
`SingleProcessIntegrationExecute` with the documented
`pdip.connection.{type,driver}` / `pdip.batch.size` /
`pdip.rows.written` attributes; (e-3) ADR-0036 **Proposed** —
checked-in deprecation manifest + two new quality_guard rules
(implementation is the ADR Follow-ups list). 100 % unit coverage
on the canonical `run_tests.py` cell (745 tests); 8
quality_guard rules green; flake8 clean across `pdip/`,
`tests/`, `scripts/`. Remaining queued items: async
iterator/paging + async write_data; spans in
`parallelthread/` + `parallelold/` strategies; integration tests
for MySQL/MSSQL/Oracle async smokes when their fixtures + extras
are present; ADR-0036 Accepted + landed. When you change
anything above, bump this line with the date and the branch
name so the next reader knows the freshness window at a glance.*
