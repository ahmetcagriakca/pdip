"""Integration smoke test for the async MSSQL connector + adapter
wiring (ADR-0032 §3 follow-up (a-2 / a-3)).

Mirrors the asyncpg Postgres smoke pattern against the
``tests/environments/mssql/`` fixture (SQL Server 2022). Skips
when ``aioodbc`` is not importable (``pdip[async]`` not installed
in the test environment) — note ``aioodbc`` itself wraps ``pyodbc``
which already requires a host-level ODBC Driver 18 install per the
sync MSSQL integration tests.

The adapter-level cases (``get_source_data_count`` /
``get_iterator`` / ``get_source_data_with_paging`` /
``write_data`` / ``do_target_operation`` / ``clear_data``)
exercise the dialect helper's MSSQL form: bracket-quoted
identifiers, ``?`` placeholders, and the ANSI
``OFFSET ... FETCH NEXT`` paging clause (which requires the
source query to carry an ``ORDER BY`` for a deterministic page).
"""

import asyncio
import unittest
from unittest import TestCase

from pdip.integrator.connection.domain.authentication.basic import (
    ConnectionBasicAuthentication,
)
from pdip.integrator.connection.domain.enums import (
    ConnectionTypes,
    ConnectorTypes,
)
from pdip.integrator.connection.domain.server.base import ConnectionServer
from pdip.integrator.connection.domain.types.sql.configuration.base import (
    SqlConnectionConfiguration,
)


def _aioodbc_available() -> bool:
    try:
        import aioodbc  # noqa: F401 — presence check only
    except ImportError:
        return False
    return True


@unittest.skipUnless(
    _aioodbc_available(),
    "pdip[async] not installed — aioodbc import unavailable",
)
class TestAsyncMssqlConnection(TestCase):
    def setUp(self):
        self.connection = SqlConnectionConfiguration(
            Name='TestAsyncMssqlConnection',
            ConnectionType=ConnectionTypes.Sql,
            ConnectorType=ConnectorTypes.MSSQL,
            Server=ConnectionServer(Host='localhost', Port=None),
            Database='master',
            BasicAuthentication=ConnectionBasicAuthentication(
                User='sa', Password='Pdi!123456'
            ),
        )

    def _run(self, coro):
        return asyncio.new_event_loop().run_until_complete(coro)

    def test_async_connector_connect_then_disconnect(self):
        from pdip.integrator.connection.types.sql.connectors.mssql.async_mssql_connector import (
            AsyncMssqlConnector,
        )
        connector = AsyncMssqlConnector(config=self.connection)

        async def _drive():
            await connector.connect()
            try:
                self.assertIsNotNone(connector.connection)
            finally:
                await connector.disconnect()
            self.assertIsNone(connector.connection)

        self._run(_drive())

    def test_async_connector_fetch_count_against_sys_tables(self):
        from pdip.integrator.connection.types.sql.connectors.mssql.async_mssql_connector import (
            AsyncMssqlConnector,
        )
        connector = AsyncMssqlConnector(config=self.connection)

        async def _drive():
            await connector.connect()
            try:
                count = await connector.fetch_count(
                    schema="sys", table="tables"
                )
                self.assertGreaterEqual(count, 0)
            finally:
                await connector.disconnect()

        self._run(_drive())

    def test_async_source_adapter_get_source_data_count_returns_int(self):
        # Drives the full chain: AsyncSqlSourceAdapter →
        # AsyncMssqlConnector → aioodbc. Uses ``sys.tables`` which
        # is always present in every database on every server.
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.source import (
            AsyncSqlSourceAdapter,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        adapter = AsyncSqlSourceAdapter()
        integration = IntegrationBase(
            SourceConnections=IntegrationConnectionBase(
                ConnectionType=ConnectionTypes.Sql,
                Sql=ConnectionSqlBase(
                    Connection=self.connection,
                    Schema="sys",
                    ObjectName="tables",
                ),
            ),
        )

        async def _drive():
            count = await adapter.get_source_data_count(integration)
            self.assertGreaterEqual(count, 0)

        self._run(_drive())

    def test_async_source_adapter_get_iterator_chunks_into_batches(self):
        # Drives ``AsyncSqlSourceAdapter.get_iterator`` against a
        # known-sized source table — verifies the chunking math
        # matches the documented batch-iteration contract. Uses
        # the adapter's generated ``SELECT * FROM [dbo].[t]`` form.
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.source import (
            AsyncSqlSourceAdapter,
        )
        from pdip.integrator.connection.types.sql.connectors.mssql.async_mssql_connector import (
            AsyncMssqlConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        schema = "dbo"
        table = "test_async_iterator_pages"
        adapter = AsyncSqlSourceAdapter()
        integration = IntegrationBase(
            SourceConnections=IntegrationConnectionBase(
                ConnectionType=ConnectionTypes.Sql,
                Sql=ConnectionSqlBase(
                    Connection=self.connection,
                    Schema=schema,
                    ObjectName=table,
                ),
            ),
        )

        async def _drive():
            setup = AsyncMssqlConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f"CREATE TABLE [{schema}].[{table}] (id INT)"
                )
                # 7 rows + limit=3 → batches [3, 3, 1].
                for i in range(1, 8):
                    await setup.execute(
                        f"INSERT INTO [{schema}].[{table}] "
                        f"VALUES ({i})"
                    )
            finally:
                await setup.disconnect()

            try:
                batches = await adapter.get_iterator(
                    integration=integration, limit=3
                )
                self.assertEqual([len(b) for b in batches], [3, 3, 1])
            finally:
                cleanup = AsyncMssqlConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await cleanup.execute(
                        f"DROP TABLE IF EXISTS [{schema}].[{table}]"
                    )
                finally:
                    await cleanup.disconnect()

        self._run(_drive())

    def test_async_source_adapter_get_source_data_with_paging(self):
        # MSSQL's ``OFFSET ... FETCH NEXT`` paging form requires
        # the base query to carry an ``ORDER BY``. We supply one
        # via the descriptor's explicit ``Sql.Query`` so the
        # adapter's ``_select_query_for`` returns it verbatim.
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.source import (
            AsyncSqlSourceAdapter,
        )
        from pdip.integrator.connection.types.sql.connectors.mssql.async_mssql_connector import (
            AsyncMssqlConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        schema = "dbo"
        table = "test_async_paging"
        adapter = AsyncSqlSourceAdapter()
        integration = IntegrationBase(
            SourceConnections=IntegrationConnectionBase(
                ConnectionType=ConnectionTypes.Sql,
                Sql=ConnectionSqlBase(
                    Connection=self.connection,
                    Schema=schema,
                    ObjectName=table,
                    Query=(
                        f"SELECT id FROM [{schema}].[{table}] ORDER BY id"
                    ),
                ),
            ),
        )

        async def _drive():
            setup = AsyncMssqlConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f"CREATE TABLE [{schema}].[{table}] (id INT)"
                )
                for i in range(1, 11):
                    await setup.execute(
                        f"INSERT INTO [{schema}].[{table}] "
                        f"VALUES ({i})"
                    )
            finally:
                await setup.disconnect()

            try:
                page = await adapter.get_source_data_with_paging(
                    integration=integration, start=2, end=7
                )
                self.assertEqual(len(page), 5)
                # Deterministic order guarantee from ORDER BY id.
                self.assertEqual(
                    [row["id"] for row in page], [3, 4, 5, 6, 7]
                )
            finally:
                cleanup = AsyncMssqlConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await cleanup.execute(
                        f"DROP TABLE IF EXISTS [{schema}].[{table}]"
                    )
                finally:
                    await cleanup.disconnect()

        self._run(_drive())

    def test_async_target_adapter_write_data_inserts_rows(self):
        # End-to-end ``write_data`` exercise: create a temp table,
        # call ``AsyncSqlTargetAdapter.write_data`` with two
        # dict-shaped rows, verify both landed by counting the
        # table, then drop it. Exercises the MSSQL placeholder
        # ladder (``?, ?``) and bracket quoting.
        from pdip.integrator.connection.domain.base import (
            ConnectionColumnBase,
        )
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.target import (
            AsyncSqlTargetAdapter,
        )
        from pdip.integrator.connection.types.sql.connectors.mssql.async_mssql_connector import (
            AsyncMssqlConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        schema = "dbo"
        table = "test_async_write_data"
        adapter = AsyncSqlTargetAdapter()
        integration = IntegrationBase(
            TargetConnections=IntegrationConnectionBase(
                ConnectionType=ConnectionTypes.Sql,
                Sql=ConnectionSqlBase(
                    Connection=self.connection,
                    Schema=schema,
                    ObjectName=table,
                ),
                Columns=[
                    ConnectionColumnBase(Name="id", Type="INT"),
                    ConnectionColumnBase(Name="name", Type="VARCHAR(50)"),
                ],
            ),
        )

        async def _drive():
            setup = AsyncMssqlConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f"CREATE TABLE [{schema}].[{table}] "
                    f"(id INT, name VARCHAR(50))"
                )
            finally:
                await setup.disconnect()

            try:
                rows_written = await adapter.write_data(
                    integration=integration,
                    source_data=[
                        {"id": 1, "name": "alice"},
                        {"id": 2, "name": "bob"},
                    ],
                )
                self.assertEqual(rows_written, 2)

                verify = AsyncMssqlConnector(config=self.connection)
                await verify.connect()
                try:
                    count = await verify.fetch_count(
                        schema=schema, table=table
                    )
                    self.assertEqual(count, 2)
                finally:
                    await verify.disconnect()
            finally:
                cleanup = AsyncMssqlConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await cleanup.execute(
                        f"DROP TABLE IF EXISTS [{schema}].[{table}]"
                    )
                finally:
                    await cleanup.disconnect()

        self._run(_drive())

    def test_async_target_adapter_do_target_operation_truncates_when_flag_set(self):
        # ``IsTargetTruncate=True`` should route do_target_operation
        # to ``clear_data``; without the flag it is a no-op
        # returning 0.
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.target import (
            AsyncSqlTargetAdapter,
        )
        from pdip.integrator.connection.types.sql.connectors.mssql.async_mssql_connector import (
            AsyncMssqlConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        schema = "dbo"
        table = "test_async_do_target_op"
        adapter = AsyncSqlTargetAdapter()

        def _make_integration(truncate: bool):
            return IntegrationBase(
                TargetConnections=IntegrationConnectionBase(
                    ConnectionType=ConnectionTypes.Sql,
                    Sql=ConnectionSqlBase(
                        Connection=self.connection,
                        Schema=schema,
                        ObjectName=table,
                    ),
                ),
                IsTargetTruncate=truncate,
            )

        async def _drive():
            setup = AsyncMssqlConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f"CREATE TABLE [{schema}].[{table}] (id INT)"
                )
                await setup.execute(
                    f"INSERT INTO [{schema}].[{table}] VALUES (1)"
                )
            finally:
                await setup.disconnect()

            try:
                noop_result = await adapter.do_target_operation(
                    integration=_make_integration(False)
                )
                self.assertEqual(noop_result, 0)
                truncate_result = await adapter.do_target_operation(
                    integration=_make_integration(True)
                )
                self.assertEqual(truncate_result, 0)

                verify = AsyncMssqlConnector(config=self.connection)
                await verify.connect()
                try:
                    post = await verify.fetch_count(
                        schema=schema, table=table
                    )
                    self.assertEqual(post, 0)
                finally:
                    await verify.disconnect()
            finally:
                cleanup = AsyncMssqlConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await cleanup.execute(
                        f"DROP TABLE IF EXISTS [{schema}].[{table}]"
                    )
                finally:
                    await cleanup.disconnect()

        self._run(_drive())

    def test_async_target_adapter_clear_data_truncates_mssql_table(self):
        # End-to-end exercise of ADR-0032 follow-up (a-3) on the
        # MSSQL target side: create a temp table, insert a row,
        # call ``AsyncSqlTargetAdapter.clear_data`` (which routes
        # to ``AsyncMssqlConnector.execute`` ``TRUNCATE TABLE`` with
        # bracket-quoted identifiers), verify the table is empty,
        # then drop the table.
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.target import (
            AsyncSqlTargetAdapter,
        )
        from pdip.integrator.connection.types.sql.connectors.mssql.async_mssql_connector import (
            AsyncMssqlConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        adapter = AsyncSqlTargetAdapter()
        schema = "dbo"
        table = "test_async_clear_data"
        integration = IntegrationBase(
            TargetConnections=IntegrationConnectionBase(
                ConnectionType=ConnectionTypes.Sql,
                Sql=ConnectionSqlBase(
                    Connection=self.connection,
                    Schema=schema,
                    ObjectName=table,
                ),
            ),
        )

        async def _setup_then_clear_then_verify():
            setup = AsyncMssqlConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f"CREATE TABLE [{schema}].[{table}] (id INT)"
                )
                await setup.execute(
                    f"INSERT INTO [{schema}].[{table}] VALUES (1)"
                )
                pre = await setup.fetch_count(schema=schema, table=table)
                self.assertEqual(pre, 1)
            finally:
                await setup.disconnect()

            try:
                result = await adapter.clear_data(integration)
                self.assertEqual(result, 0)

                verify = AsyncMssqlConnector(config=self.connection)
                await verify.connect()
                try:
                    post = await verify.fetch_count(
                        schema=schema, table=table
                    )
                    self.assertEqual(post, 0)
                finally:
                    await verify.disconnect()
            finally:
                cleanup = AsyncMssqlConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await cleanup.execute(
                        f"DROP TABLE IF EXISTS [{schema}].[{table}]"
                    )
                finally:
                    await cleanup.disconnect()

        self._run(_setup_then_clear_then_verify())
