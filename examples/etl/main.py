"""Minimal pdip ETL example — copy rows between two SQLite databases.

Run from the repo root:

    python examples/etl/main.py

What this example shows
-----------------------

The smallest possible "real" ETL flow that exercises pdip's
``InMemoryProvider`` connection abstraction (no external database,
no docker, no API key). Two SQLite database files act as source
and target; the script:

1. Opens an ``InMemoryProvider`` SQLite context per database.
2. Creates a ``contacts`` table on both sides (idempotent).
3. Seeds the source table with three rows.
4. Reads the source rows into a Python list and writes them to the
   target via ``execute_many`` — the same primitive every SQL
   adapter under ``pdip.integrator.connection.types.sql`` exposes.
5. Reads the target rows back and prints them.

It deliberately stops short of constructing a full
``OperationBase`` / ``Integrator`` object graph (the heavier path
the ``tests/integrationtests/integrator/integration/sql/<backend>/``
modules use for cross-database copy operations). For a real
production flow you would assemble that graph and let the
``Integrator`` orchestrate parallel readers / writers; the README
explains the trade-off and points at the integration tests as the
next step up.

This file is exercised by
``tests/unittests/examples/etl/test_etl_example.py`` so CI catches
any framework change that regresses the demo.
"""

import os
import sys
import tempfile

# When invoked as ``python examples/etl/main.py`` Python adds only
# the script's own directory to ``sys.path``. Prepend the repo root
# so ``from pdip…`` and ``from examples…`` resolve the same way
# they do under ``unittest`` / pytest.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from pdip.integrator.connection.domain.enums import ConnectorTypes  # noqa: E402
from pdip.integrator.connection.types.inmemory.base import InMemoryProvider  # noqa: E402


def _open_context(path):
    """Return a connected ``InMemoryProvider`` SQLite context for ``path``."""

    context = InMemoryProvider().get_context(
        connector_type=ConnectorTypes.SqLite,
        database=path,
    )
    context.connector.connect()
    return context


def _create_contacts_table(context):
    """Idempotent ``contacts`` table creation."""

    context.execute(
        "CREATE TABLE IF NOT EXISTS contacts ("
        " id INTEGER PRIMARY KEY,"
        " name TEXT NOT NULL,"
        " email TEXT NOT NULL"
        ")"
    )


def run(source_path, target_path):
    """Copy three seeded rows from ``source_path`` to ``target_path``.

    Returns the list of dict rows that ended up in the target so the
    caller / test can assert on the result without re-querying.
    """

    source = _open_context(source_path)
    target = _open_context(target_path)

    _create_contacts_table(source)
    _create_contacts_table(target)

    # Truncate both sides so the example is idempotent across runs.
    source.execute("DELETE FROM contacts")
    target.execute("DELETE FROM contacts")

    seed_rows = [
        (1, "Ada Lovelace", "ada@example.com"),
        (2, "Alan Turing", "alan@example.com"),
        (3, "Grace Hopper", "grace@example.com"),
    ]
    source.execute_many(
        "INSERT INTO contacts (id, name, email) VALUES (?, ?, ?)",
        seed_rows,
    )

    # Extract from source. ``fetch_query`` returns a list of dict
    # rows keyed by column name — the cross-adapter shape the
    # integrator's source readers consume.
    extracted = source.fetch_query("SELECT id, name, email FROM contacts ORDER BY id")

    # Load into target. Re-tuple the dicts so ``execute_many``'s
    # parameter binding receives the positional shape SQLite expects.
    target.execute_many(
        "INSERT INTO contacts (id, name, email) VALUES (?, ?, ?)",
        [(row["id"], row["name"], row["email"]) for row in extracted],
    )

    final = target.fetch_query("SELECT id, name, email FROM contacts ORDER BY id")
    return final


def main():
    workdir = tempfile.mkdtemp(prefix="pdip-etl-example-")
    source_path = os.path.join(workdir, "source.db")
    target_path = os.path.join(workdir, "target.db")
    print(f"Working directory: {workdir}")

    rows = run(source_path, target_path)

    print(f"Copied {len(rows)} rows into {target_path}:")
    for row in rows:
        print(f"  {row['id']:>2}  {row['name']:<14}  {row['email']}")


if __name__ == "__main__":
    main()
