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
| Integration CI | Nightly 04:00 UTC + `workflow_dispatch` + workflow self-test PR trigger; runs Postgres 16, MySQL 8.4, Oracle XE 21c | [`.github/workflows/integration-tests.yml`](../.github/workflows/integration-tests.yml), [ADR-0029](governance/adr/0029-integration-tests-in-ci.md) |
| Pre-commit | `pre-commit install` runs the 6 ADR-0026/0027 §5 quality rules + blocking flake8 in ~300 ms | [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) |

## 2. Open PRs

| # | What | Next action | Why deferred |
|---|---|---|---|
| [#64](https://github.com/ahmetcagriakca/pdip/pull/64) | Dependabot: `oracledb >=2,<4` (allow 3.x) | **Decide on the upper bound.** Adapter migration to 3.x is a separate ADR — see §4. Hold or merge after a manual smoke against the new Oracle XE nightly job. | Driver bumps for integrator adapters are excluded from auto-merge per [ADR-0025 §3](governance/adr/0025-dependabot-auto-merge-policy.md). |
| [#63](https://github.com/ahmetcagriakca/pdip/pull/63) | Dependabot: `markupsafe 2.1.5 → 3.0.3` | Auto-merge if CI green; transitively used via Flask/Jinja, no direct `import markupsafe` in `pdip/`. | — |
| [#61](https://github.com/ahmetcagriakca/pdip/pull/61) | Dependabot: `pyodbc 5.1.0 → 5.3.0` | **Hold** until MSSQL nightly job lands (§4) so the bump has a regression signal. | Same ADR-0025 §3 carve-out as #64. |

## 3. Branches

The active branch for the next handoff iteration is documented at the bottom
of this file. Most `claude/*` branches on the remote are post-merge
artifacts from squash-merged PRs — safe to ignore unless a name below is
listed. **Reserved (not yet pushed):**

- `claude/integration-tests-adaptive-schedule` — reserved for the ADR-0029
  §6 follow-up (open an issue on two consecutive red nights). No commits
  yet; create when picking the work up.

If you find a `claude/*` branch not listed here and not associated with an
open PR, it is almost certainly stale — confirm with `git log
origin/main..origin/<branch>` before deleting.

## 4. Deferred decisions

Each row is something we *intentionally did not do*. Pick one up with an
ADR if the answer changed.

| Topic | Status | Pointer |
|---|---|---|
| `oracledb` 4.x adoption | Upper bound bump pending in [#64](https://github.com/ahmetcagriakca/pdip/pull/64). 4.x has not been audited against [ADR-0021](governance/adr/0021-cx-oracle-to-python-oracledb.md)'s adapter contract. | Manual smoke + adapter contract review before merging the upper-bound bump. |
| MSSQL 2022 nightly job | Listed under [ADR-0029 Follow-ups](governance/adr/0029-integration-tests-in-ci.md). Needs `ACCEPT_EULA=Y` and an SA-login health probe. | Separate PR; image already pinned in `tests/environments/mssql/`. |
| Kafka 7.7.1 + ZooKeeper nightly job | [ADR-0029 Follow-ups](governance/adr/0029-integration-tests-in-ci.md). Two-service composition + topic-create step. | Separate PR; image already pinned. |
| Hadoop / Impala fixtures | Marked `# unmaintained` in `tests/environments/`. ADR-0029 explicitly defers their integration-test job until images are migrated. | Migration plan ADR first, then job. |
| `examples/etl` + pub/sub observer demo | Listed in [`examples/README.md`](../examples/README.md) as planned follow-ups to `examples/crud_api`. | None — pick up when the next end-to-end story needs an executable reference. |
| Async / OpenTelemetry / 1.0 cut | No ADR drafted. Mentioned as long-horizon items in conversation; not on any milestone. | Open as ADR-0030+ when an actual driver appears. |

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

*Last updated on the branch that introduced this file
(`claude/add-handoff-docs-3qZYI`). When you change anything above, bump
this line with the date and the branch name so the next reader knows the
freshness window at a glance.*
