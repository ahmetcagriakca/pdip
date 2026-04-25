# Integration-test backing services

Docker-compose fixtures for the databases and brokers that
`tests/integrationtests/` exercises. Pulled in locally by contributors
who want to reproduce an integration-test failure, and (planned,
ADR-0029 follow-up) by the scheduled CI workflow that runs them
nightly.

Image versions are pinned to current LTS / stable releases. Dependabot
(per [ADR-0025](../../docs/governance/adr/0025-dependabot-auto-merge-policy.md))
tracks the Docker ecosystem and opens weekly PRs when a new tag lands.

## Backends and pins

| Backend | Image | Default port | Credentials | Maintained? |
|---|---|---|---|---|
| MySQL | `mysql:8.4` (LTS till 2032-04) | 3306 | `pdi / pdi!123456 / test_pdi` | ✅ |
| PostgreSQL | `postgres:16-alpine` | 5434 → 5432 | `pdi / pdi!123456 / test_pdi` | ✅ |
| SQL Server | `mcr.microsoft.com/mssql/server:2022-latest` | 1433 | `sa / yourStrong(!)Password` | ✅ |
| Oracle XE | `gvenzl/oracle-xe:21-slim-faststart` | 1521 | `pdi / pdi!123456 / test_pdi` | ✅ |
| Kafka | `confluentinc/cp-kafka:7.7.1` + `cp-zookeeper:7.7.1` | 29092 (host), 9092 (inter-broker) | no auth | ✅ |
| Impala | `apache/impala:4.5.0-impala_quickstart_hms` + `-statestored` + `-catalogd` + `-impalad_coord_exec` | 21050 (HS2), 25000 (debug UI) | no auth | ⚠ compose translated from upstream `apache/impala/docker/quickstart.yml`, **not yet locally validated** — see ADR-0030 |

## Boot + tear-down recipe

Each backend has its own `docker-compose.yml`. Start / stop one in
isolation:

```bash
cd tests/environments/<backend>
docker compose up -d
# ... run integration tests pointed at this backend ...
docker compose down --volumes   # --volumes discards persisted data
```

For the MySQL / PostgreSQL / MSSQL / Oracle fixtures the host port in
the table above is exactly what the corresponding test module under
`tests/integrationtests/integrator/integration/sql/<backend>/` expects,
so "boot + run" works end-to-end without editing tests.

## Running against a remote database

The hardcoded credentials in the test modules are convenient for the
fixture, but they're not sacred. If you need to run the integration
tests against a remote instance (e.g. a staging Oracle), edit the
`SqlConnectionConfiguration(...)` block in the relevant test to point
at your host / credentials before running.

## Unmaintained-image policy

The `bigdata/impala/` fixture has been **migrated to Apache-official
`apache/impala:4.5.0-*` images** as part of [ADR-0030](../../docs/governance/adr/0030-hadoop-impala-fixture-migration.md)
Stage 1. The compose is a faithful translation of the upstream
[`apache/impala/docker/quickstart.yml`](https://github.com/apache/impala/tree/master/docker)
(HMS + statestored + catalogd + impalad_coord_exec) with the
single config file (`hive-site.xml`) vendored under `quickstart_conf/`.
The `parrotstream/kudu` services were dropped — no Impala test today
exercises Kudu code paths; ADR-0030 Stage 2 re-introduces a
maintained `apache/kudu:1.17.0` if a future test needs it.

**The new compose has not yet been booted locally** by the session
that wrote it (no Docker daemon was available); the next contributor
running `docker compose up` should confirm `localhost:21050` accepts
a pyodbc connection before merging anything that depends on the
fixture. Until that validation lands, treat the fixture as draft.

The previously-listed `hadoop/` fixture
(`bde2020/hadoop-*:2.0.0-hadoop3.2.1-java8`) was deleted in the
Stage 1 mechanical-cleanup PR — no test under `tests/integrationtests/`
referenced it (the bigdata tests target Impala only, and Apache
Impala 4.x's local-fs storage mode removes the external HDFS
dependency the old fixture provided). Reviving an HDFS-only fixture
would open its own ADR.
