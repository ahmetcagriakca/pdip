# pdip ETL example — SQLite source → SQLite target

The smallest possible "real" ETL flow that exercises pdip's
`InMemoryProvider` connection abstraction without an external
database, docker, or API key. Two SQLite database files act as
source and target; `main.py` seeds three rows, copies them across,
and prints what landed.

## Run it

From the repo root after `pip install -e ".[integrator]"`:

```bash
python examples/etl/main.py
```

Expected output (paths will vary):

```
Working directory: /tmp/pdip-etl-example-…
Copied 3 rows into /tmp/pdip-etl-example-…/target.db:
   1  Ada Lovelace    ada@example.com
   2  Alan Turing     alan@example.com
   3  Grace Hopper    grace@example.com
```

## What it shows (and what it deliberately doesn't)

This example demonstrates pdip's **connection abstraction layer** —
the `InMemoryProvider` factory, the `ConnectorTypes.SqLite` enum,
and the cross-adapter `execute` / `execute_many` / `fetch_query`
primitives that every SQL adapter under
`pdip.integrator.connection.types.sql` exposes.

It does **not** assemble a full `OperationBase` / `Integrator`
object graph. The real production ETL pattern stitches together
`OperationIntegrationBase` steps (create-target, load-data,
drop-temp) and lets the `Integrator` orchestrate parallel readers
and writers — the heavier path the
[`tests/integrationtests/integrator/integration/sql/<backend>/`](../../tests/integrationtests/integrator/integration/sql)
modules use for cross-database copy operations against real
Postgres / MySQL / Oracle / SQL Server backends.

Once you can read `main.py` and follow the data flow, the next
step up is to read one of those integration tests (Postgres is the
shortest) — the connection-construction shape is identical, and
the operation graph layers on top.

## Why SQLite for the demo

- No external dependency, no docker, no port conflicts.
- The `InMemoryProvider` is the same factory production code
  reaches for when running pdip's own unit tests (`tests/integrationtests/integrator/connection/inmemory/sqlite/test_connection.py`),
  so the example mirrors a code path that is already exercised in
  CI.
- File-backed SQLite paths work across all supported Python
  versions (3.10–3.14) without per-platform tweaks.
