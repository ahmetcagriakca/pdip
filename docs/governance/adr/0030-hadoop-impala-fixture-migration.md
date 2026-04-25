# ADR-0030: Migrate the Hadoop / Impala / Kudu fixtures off unmaintained images

- **Status:** Proposed
- **Date:** 2026-04-25
- **Deciders:** pdip maintainers
- **Tags:** testing, ci, fixtures, bigdata
- **Relates to:** [ADR-0023](./0023-coverage-floor-policy.md) (the
  bigdata adapter paths it eventually fills in for),
  [ADR-0029](./0029-integration-tests-in-ci.md) (the Follow-ups bullet
  this ADR resolves), [ADR-0025](./0025-dependabot-auto-merge-policy.md)
  (the Docker ecosystem coverage that lands subsequent bumps once
  pins point at maintained tags).

## Context

Two of the seven backends in `tests/environments/` are pinned to
images that have not received an upstream update since 2020:

| Backend | Current pin | Last upstream update |
|---|---|---|
| Hadoop (5 services) | `bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8` (and matching `-datanode`, `-resourcemanager`, `-nodemanager`, `-historyserver`) | 2020 |
| Impala | `ibisproject/impala` (no version tag — effectively rolling, but the source repo is archived) | 2020 |
| Kudu (master + tserver) | `parrotstream/kudu:latest` | 2020 |

Both compose files carry an explicit `# unmaintained; see header`
marker (added in PR #97 as part of the docker-compose stabilisation
sweep), and ADR-0029's `## Follow-ups` block calls this out:

> Consider migrating the Hadoop / Impala bigdata fixtures to
> maintained images before adding their integration-test jobs.

That is the gate this ADR addresses. Without maintained images:

1. **No nightly job.** ADR-0029 deliberately stopped short of adding
   a `bigdata:` job because pointing CI at archived images would
   start failing the moment Docker Hub garbage-collects them. The
   adapter under `pdip/integrator/connection/types/bigdata/connectors/impala/`
   stays uncovered by integration tests as a result.
2. **No driver-bump regression signal.** Future `pyodbc` /
   `confluent-kafka` / `cloudera-impala-odbc` bumps that touch the
   Impala adapter land with the same blind spot ADR-0029 closed for
   Postgres / MySQL / Oracle.
3. **Bit-rot in slow motion.** A stale third-party image that
   silently disappears from the registry breaks the local
   reproduction recipe documented in `tests/environments/README.md`,
   not just CI.

The pdip-side surface that has to keep working is narrow:
`ImpalaConnector` is a thin pyodbc wrapper (`pdip/integrator/connection/types/bigdata/connectors/impala/impala_connector.py`)
that builds a Cloudera-style ODBC connection string and runs
`SELECT` / `EXECUTE` through it. The existing tests at
`tests/integrationtests/integrator/integration/bigdata/impala/`
boot a cluster, write a small dataset, and read it back. Hadoop is
an *implementation detail* of the Impala fixture (HDFS for the
Impala daemon to read from); Kudu is its storage engine. The
adapter never talks to HDFS or Kudu directly.

That observation widens the migration's design space: we are not
obliged to keep three separate compose files in lockstep — we have
to keep an Impala-compatible ODBC endpoint reachable on port
`21050` plus a backing store the daemon trusts.

## Decision

We migrate the bigdata fixtures in three sequenced PRs, each
independently mergeable, none required by the others to keep `main`
green:

### Stage 1 — collapse to a single Impala fixture

Replace `tests/environments/bigdata/impala/docker-compose.yml` with a
two-service compose that runs the Apache-official `apache/impala`
image (released 4.x; tags published since 2024) against the same
`postgres:16-alpine` metastore the current fixture already uses.
Rationale: Apache Impala 4.x ships an embedded local-fs storage
mode for development clusters, so the daemon no longer needs an
external HDFS to start. The `bde2020/hadoop-*` services become
obsolete.

`tests/environments/hadoop/` is deleted in the same PR — once
nothing depends on it, leaving it around is dead weight that
Dependabot keeps trying to update.

`tests/environments/README.md`'s "Backends and pins" table loses
the Hadoop row and changes the Impala row's `Maintained?` column
from `⚠` to `✅`.

### Stage 2 — replace the Kudu fixture if still needed

Apache Kudu publishes a maintained `apache/kudu:1.17.0` image. If
the Impala fixture from Stage 1 covers the integration tests
without Kudu (the existing tests do not exercise Kudu-specific
features as far as the test code shows — they test SELECT / INSERT
flow that local-fs Impala storage handles), drop the Kudu compose
entirely. If a test does need Kudu, re-introduce it as a separate
service in the same compose file using `apache/kudu:1.17.0`.

This stage is conditional on Stage 1's audit: a contributor running
the existing tests against the new fixture confirms which (if any)
Kudu features are reached.

### Stage 3 — wire the bigdata nightly job

With both fixtures pointing at maintained, version-pinned images,
add an `impala:` job to `.github/workflows/integration-tests.yml`
mirroring the `postgres:` / `mysql:` / `oracle:` / `mssql:`
pattern. The runner installs the **Cloudera Impala ODBC driver**
(or whichever ODBC driver `find_driver_name` resolves to in the
Apache 4.x build), boots the compose-defined services as Actions
`services:` containers, and runs
`tests/integrationtests/integrator/integration/bigdata/impala/`.

This is the bullet ADR-0029's Follow-ups list defers to *this* ADR.

## Consequences

### Positive

- The bigdata adapter joins the four SQL backends already covered by
  nightly CI. Driver-bump regressions surface within 24 hours rather
  than at the next downstream bug report.
- Dependabot's Docker ecosystem (added in PR #95) starts tracking
  meaningful targets — `apache/impala`, `apache/kudu`, the
  `postgres:16-alpine` metastore — instead of effectively pinned
  zombies.
- One compose file replaces six (one Impala + zero–one Kudu vs. five
  Hadoop + one Impala + two Kudu). Less surface, less drift.
- `tests/environments/README.md`'s "Maintained?" column becomes a
  monotone ✅, removing the open-ended footnote.

### Negative

- **Audit required up-front.** We do not yet *know* that
  `apache/impala:4.x` runs standalone on a single Actions runner
  within the 15-minute timeout that frames the SQL backends. The
  Stage 1 PR carries that audit; if the image needs a beefier
  runner or a longer warm-up than `services:` allows, the plan
  forks to "use a self-hosted runner" or "scope down to a unit-only
  bigdata adapter test", neither of which is in scope for this ADR.
- **Existing tests may need to declare a bigdata-only flag.** If
  Impala 4.x's local-fs mode boots slower than the SQL backends
  (~minutes rather than seconds), the bigdata job's timeout grows
  proportionally. The job is nightly, not per-PR, so the impact is
  bounded.
- **Cloudera ODBC driver licensing.** The ODBC driver Stage 3 needs
  is shipped under a Cloudera EULA (free for use; not redistributable).
  The runner step downloads it from Cloudera's public URL with the
  same `ACCEPT_EULA=Y` shape the MSSQL job uses for `msodbcsql18`.
  No change to redistribution; the driver is fetched on the runner,
  not vendored.

### Neutral

- Hadoop disappears from the repo. Any future need for an HDFS-only
  fixture (e.g. testing a hypothetical pdip HDFS adapter) opens its
  own ADR for the migration; reviving `bde2020/*` is explicitly off
  the table.
- The "5-service Hadoop cluster" was load-bearing exactly nowhere
  outside the Impala fixture, so its removal does not affect any
  pdip code path.

## Alternatives considered

### Option A — Keep `bde2020/hadoop-*` and `ibisproject/impala`, hope they survive

- **Pro:** Zero work today.
- **Con:** Image pulls already inherit no security patches since 2020;
  Docker Hub's image-retention policy could remove either upstream
  publisher account at any time, breaking the local reproduction
  recipe and any CI plan based on it. ADR-0029's Follow-ups bullet
  exists precisely so we don't take this gamble.
- **Why rejected:** Defers a problem that grows.

### Option B — Replace Impala with Trino

- **Pro:** Trino is actively maintained, ships first-party Docker
  images, and exposes the same ODBC surface the pdip adapter
  consumes (Cloudera ODBC driver works against Trino with minor
  config changes).
- **Con:** Different SQL dialect (Trino is ANSI-leaning; Impala has
  HiveQL ancestry). The existing test queries would need a
  dialect-translation pass, and the adapter's `Driver=...` discovery
  changes. The user-facing documentation that promises an "Impala
  adapter" would also need updating.
- **Why rejected for now:** Larger blast radius than necessary.
  This ADR's goal is "maintained fixture for the existing adapter,"
  not "different bigdata backend". Trino can be revisited as ADR-0031
  if Apache Impala's image proves unsuitable.

### Option C — Switch the adapter from Impala to Hive

- **Pro:** `apache/hive:4.0.0` is well-maintained.
- **Con:** Hive has different semantics from Impala on the analytical
  workloads the adapter targets, and rewriting an adapter is a code
  change, not a fixture change. Out of scope.
- **Why rejected:** Wrong layer.

## Follow-ups

- **Stage 1 PR** — replace `tests/environments/bigdata/impala/docker-compose.yml`,
  delete `tests/environments/hadoop/`, update
  `tests/environments/README.md`. Status: pending audit.
- **Stage 2 PR (conditional)** — Kudu service re-introduction if the
  existing tests need it. Likely a one-line addition to the Stage 1
  compose file.
- **Stage 3 PR** — `impala:` job in
  `.github/workflows/integration-tests.yml`, plus a CHANGELOG entry
  closing the ADR-0029 Follow-ups bullet.
- **Documentation** — once Stage 3 lands, this ADR's status moves
  from `Proposed` to `Accepted — Implemented YYYY-MM-DD (PR #N)`,
  matching the ADR-0021 / ADR-0022 implementation-stamp convention.

## References

- Code: `pdip/integrator/connection/types/bigdata/connectors/impala/impala_connector.py`
- Tests: `tests/integrationtests/integrator/integration/bigdata/impala/`
- Fixtures: `tests/environments/hadoop/docker-compose.yml`,
  `tests/environments/bigdata/impala/docker-compose.yml`
- ADR-0029 §Follow-ups bullet: `docs/governance/adr/0029-integration-tests-in-ci.md`
- Apache Impala project: <https://impala.apache.org/>
- Apache Kudu project: <https://kudu.apache.org/>
