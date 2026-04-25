# ADR-0030: Migrate the Hadoop / Impala / Kudu fixtures off unmaintained images

- **Status:** Proposed (revised 2026-04-25 after a Docker Hub audit
  reframed Stage 1 — see *Decision §Stage 1* and the *Revision
  history* footer)
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

### Stage 1 — translate Apache Impala's `quickstart.yml` into the fixture

Replace `tests/environments/bigdata/impala/docker-compose.yml` with a
**multi-component compose** modelled on the upstream
[`apache/impala/docker/quickstart.yml`](https://github.com/apache/impala/tree/master/docker).
The Apache project does **not** ship a single all-in-one Impala
image; the `apache/impala:4.5.0-*` family on Docker Hub is
componentised. A minimal cluster needs roughly the following
service set, all pinned to `4.5.0`:

| Service | Image | Purpose |
|---|---|---|
| `postgres` | `postgres:16-alpine` (already pinned in the existing fixture) | Hive Metastore Service backing store |
| `hive-metastore` | `apache/impala:4.5.0-impala_quickstart_hms` | Hive Metastore daemon (~1.82 GB image) |
| `statestored` | `apache/impala:4.5.0-statestored` | Cluster membership / state |
| `catalogd` | `apache/impala:4.5.0-catalogd` | Metadata cache |
| `impala` | `apache/impala:4.5.0-impalad_coord_exec` | Combined coordinator + executor; exposes the SQL endpoint on `21050` |

Rationale: Apache Impala 4.x exposes a **local-filesystem storage
mode** that removes the external HDFS dependency the current
`bde2020/hadoop-*` cluster carries. The 5-component split is
heavier than this ADR's first revision claimed (which incorrectly
assumed a single all-in-one image), but it is still a strict win
on three axes:

- All five images are **maintained** by Apache and version-pinned.
- No external Hadoop substrate — the fixture goes from `5 Hadoop +
  1 Impala + 2 Kudu = 8 containers` to `1 Postgres + 4 Impala = 5
  containers`.
- Boot ordering is fully described by the upstream `quickstart.yml`
  (HMS depends on Postgres, statestored runs first, catalogd reads
  HMS, impalad reads catalogd) — translating it to GitHub Actions
  `services:` is mechanical, not a research project.

`tests/environments/hadoop/` is deleted in the same PR — once
nothing depends on it, leaving it around is dead weight that
Dependabot keeps trying to update.

`tests/environments/README.md`'s "Backends and pins" table loses
the Hadoop row and changes the Impala row's `Maintained?` column
from `⚠` to `✅`. The maintainer running the audit should also
verify against the upstream `quickstart.yml` whether any newer
`4.5.x` patch tag has shipped — Dependabot will then track it from
the next bump.

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
  meaningful targets — `apache/impala:4.5.0-*`, `apache/kudu`, the
  `postgres:16-alpine` metastore — instead of effectively pinned
  zombies.
- Container count drops from `5 Hadoop + 1 Impala + 2 Kudu = 8` to
  `1 Postgres + 4 Impala (+ 0–2 Kudu) = 5–7`. Less surface, less
  drift, all images on a maintained release line.
- `tests/environments/README.md`'s "Maintained?" column becomes a
  monotone ✅, removing the open-ended footnote.

### Negative

- **5-service Actions block, not a single one.** The fixture is
  more lines of YAML than any other backend in
  `.github/workflows/integration-tests.yml`. Each service needs the
  right env vars, port mappings, and (where relevant) a
  `--health-cmd`; mistakes show up as silent broker-style boot
  loops. The Stage 3 PR is correspondingly larger than the
  Postgres / MySQL / Oracle / MSSQL ones.
- **HMS image weight.** `apache/impala:4.5.0-impala_quickstart_hms`
  is ~1.82 GB. Service-container pull on a cold runner adds ~30–60 s
  per nightly. The cost is bounded (it's nightly, not per-PR) but
  not free.
- **Boot ordering is real.** The Apache `quickstart.yml` declares
  `depends_on` between postgres → HMS → statestored → catalogd →
  impalad. GitHub Actions `services:` does not honour `depends_on`
  — services boot in parallel. Stage 3 has to either wait through a
  Python readiness probe (the pattern Oracle / MSSQL already use)
  or emulate the depends-on chain with `--health-cmd` per service.
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
- Apache Impala Docker quickstart: <https://github.com/apache/impala/tree/master/docker>
- Apache Kudu project: <https://kudu.apache.org/>

## Revision history

- **2026-04-25** (initial proposal). Stage 1 framed as "collapse to
  a *single* Apache-official Impala fixture" against `apache/impala`
  + `postgres:16-alpine`. Implementation prerequisite check skipped.
- **2026-04-25** (Docker Hub audit, same day). Stage 1 reframed:
  Apache does not ship a single all-in-one Impala image; the
  `apache/impala:4.5.0-*` family is componentised
  (HMS / statestored / catalogd / impalad). The minimal fixture is
  4–5 services modelled on upstream `quickstart.yml`, not the
  two-service compose the initial wording suggested. The win is
  smaller than first claimed (5–7 maintained containers vs. 8
  unmaintained ones, not "one fixture replaces six"), but the
  direction holds: maintained images, no external HDFS, version
  pins Dependabot can track. Stage 3's Negative consequences
  expanded with the realities of multi-service boot ordering on
  Actions and the HMS image's ~1.82 GB pull cost.
