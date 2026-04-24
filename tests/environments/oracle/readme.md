# Oracle XE 21c — local integration-test fixture

Boots an Oracle Database Express Edition 21c instance via
[`gvenzl/oracle-xe`](https://github.com/gvenzl/oci-oracle-xe), a
community-maintained image tuned for CI use. Previous fixture used
`daggerok/oracle:se`, an unmaintained third-party image; see the
header of `docker-compose.yml` for the bump rationale.

## Boot

```bash
cd tests/environments/oracle
docker compose up -d
# first boot initialises the database — ~40 s on the ``faststart``
# variant. ``docker compose logs -f oracle-xe`` will show
# "DATABASE IS READY TO USE!" when it's done.
```

## Connect

| Setting | Value |
|---|---|
| Host | `localhost` |
| Port | `1521` |
| Service / PDB | `test_pdi` |
| SYS / SYSTEM password | `pdi!123456` |
| App user | `pdi` |
| App user password | `pdi!123456` |

`python-oracledb` (per
[ADR-0021](../../../docs/governance/adr/0021-cx-oracle-to-python-oracledb.md))
runs in thin mode against this fixture — no Instant Client needed.

## Provisioning the schema

`scripts.sql` in this directory sets up the test schema. Run it
once after first boot:

```bash
docker compose exec oracle-xe \
    bash -c "sqlplus pdi/pdi\!123456@//localhost:1521/test_pdi @/container-entrypoint-initdb.d/scripts.sql"
```

## Tear down

```bash
docker compose down --volumes
```
