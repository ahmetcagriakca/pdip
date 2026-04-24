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
| Hadoop | `bde2020/hadoop-*:2.0.0-hadoop3.2.1-java8` | 9000 / 9870 | no auth | ⚠ unmaintained since 2020; follow-up migration pending |
| Impala + Kudu | `ibisproject/impala`, `parrotstream/kudu:latest` | 21050 (Impala), 7051 (Kudu master) | no auth | ⚠ unmaintained; same follow-up as Hadoop |

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

Two fixtures (`hadoop/`, `bigdata/impala/`) sit on third-party images
that stopped receiving updates around 2020. We leave them pinned to
their last-known-good tag with a `# unmaintained; see header` marker
in-line. Any new big-data integration test should either (a) add its
backend as a new subdirectory with a maintained image, or (b) wait
for the migration PR that replaces Hadoop/Impala with Apache-official
or modern alternatives.
