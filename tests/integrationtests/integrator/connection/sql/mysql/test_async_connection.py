"""Integration smoke test for the async MySQL connector + adapter
wiring (ADR-0032 §3 follow-up (a-2 / a-3)).

Mirrors the asyncpg Postgres smoke test pattern against the
``tests/environments/mysql/`` fixture (MySQL 8.4 on
``localhost:3306``). Skips when ``aiomysql`` is not importable
(``pdip[async]`` not installed in the test environment).

The adapter-level cases (``get_source_data_count`` /
``get_iterator`` / ``get_source_data_with_paging`` /
``write_data`` / ``do_target_operation`` / ``clear_data``)
exercise the dialect helper's MySQL form: backtick-quoted
identifiers, ``%s`` placeholders, and the standard LIMIT/OFFSET
paging.
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


def _aiomysql_available() -> bool:
    try:
        import aiomysql  # noqa: F401 — presence check only
    except ImportError:
        return False
    return True


@unittest.skipUnless(
    _aiomysql_available(),
    "pdip[async] not installed — aiomysql import unavailable",
)
class TestAsyncMysqlConnection(TestCase):
    def setUp(self):
        self.connection = SqlConnectionConfiguration(
            Name='TestAsyncMysqlConnection',
            ConnectionType=ConnectionTypes.Sql,
            ConnectorType=ConnectorTypes.MYSQL,
            Server=ConnectionServer(Host='localhost', Port='3306'),
            Database='test_pdi',
            BasicAuthentication=ConnectionBasicAuthentication(
                User='pdi', Password='pdi!123456'
            ),
        )

    def _run(self, coro):
        return asyncio.new_event_loop().run_until_complete(coro)

    def test_async_connector_connect_then_disconnect(self):
        from pdip.integrator.connection.types.sql.connectors.mysql.async_mysql_connector import (
            AsyncMysqlConnector,
        )
        connector = AsyncMysqlConnector(config=self.connection)

        async def _drive():
            await connector.connect()
            try:
                self.assertIsNotNone(connector.connection)
            finally:
                await connector.disconnect()
            self.assertIsNone(connector.connection)

        self._run(_drive())

    def test_async_connector_fetch_count_against_information_schema(self):
        from pdip.integrator.connection.types.sql.connectors.mysql.async_mysql_connector import (
            AsyncMysqlConnector,
        )
        connector = AsyncMysqlConnector(config=self.connection)

        async def _drive():
            await connector.connect()
            try:
                count = await connector.fetch_count(
                    schema="information_schema", table="TABLES"
                )
                self.assertGreater(count, 0)
            finally:
                await connector.disconnect()

        self._run(_drive())

    def test_async_source_adapter_get_source_data_count_returns_int(self):
        # Drives the full chain: AsyncSqlSourceAdapter →
        # AsyncMysqlConnector → aiomysql. Uses
        # ``information_schema.TABLES`` which is always present and
        # has a deterministic non-zero row count.
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
                    Schema="information_schema",
                    ObjectName="TABLES",
                ),
            ),
        )

        async def _drive():
            count = await adapter.get_source_data_count(integration)
            self.assertGreater(count, 0)

        self._run(_drive())

    def test_async_source_adapter_get_iterator_chunks_into_batches(self):
        # Drives ``AsyncSqlSourceAdapter.get_iterator`` against a
        # known-sized source table — verifies the chunking math
        # matches the documented batch-iteration contract.
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.source import (
            AsyncSqlSourceAdapter,
        )
        from pdip.integrator.connection.types.sql.connectors.mysql.async_mysql_connector import (
            AsyncMysqlConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        schema = "test_pdi"
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
            setup = AsyncMysqlConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f"CREATE TABLE `{schema}`.`{table}` (id INT)"
                )
                # 7 rows + limit=3 → batches [3, 3, 1].
                for i in range(1, 8):
                    await setup.execute(
                        f"INSERT INTO `{schema}`.`{table}` "
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
                cleanup = AsyncMysqlConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await cleanup.execute(
                        f"DROP TABLE IF EXISTS `{schema}`.`{table}`"
                    )
                finally:
                    await cleanup.disconnect()

        self._run(_drive())

    def test_async_source_adapter_get_source_data_with_paging(self):
        # ``LIMIT/OFFSET`` form against information_schema.TABLES,
        # which has a stable ordering guarantee for our purposes
        # (no writes between calls).
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
                    Schema="information_schema",
                    ObjectName="TABLES",
                ),
            ),
        )

        async def _drive():
            page = await adapter.get_source_data_with_paging(
                integration=integration, start=0, end=5
            )
            self.assertEqual(len(page), 5)

        self._run(_drive())

    def test_async_target_adapter_write_data_inserts_rows(self):
        # End-to-end ``write_data`` exercise: create a temp table,
        # call ``AsyncSqlTargetAdapter.write_data`` with two
        # dict-shaped rows, verify both landed by counting the
        # table, then drop it. Exercises the MySQL placeholder
        # ladder (``%s, %s``) and backtick quoting.
        from pdip.integrator.connection.domain.base import (
            ConnectionColumnBase,
        )
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.target import (
            AsyncSqlTargetAdapter,
        )
        from pdip.integrator.connection.types.sql.connectors.mysql.async_mysql_connector import (
            AsyncMysqlConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        schema = "test_pdi"
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
                    ConnectionColumnBase(Name="name", Type="varchar(50)"),
                ],
            ),
        )

        async def _drive():
            setup = AsyncMysqlConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f"CREATE TABLE `{schema}`.`{table}` "
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

                verify = AsyncMysqlConnector(config=self.connection)
                await verify.connect()
                try:
                    count = await verify.fetch_count(
                        schema=schema, table=table
                    )
                    self.assertEqual(count, 2)
                finally:
                    await verify.disconnect()
            finally:
                cleanup = AsyncMysqlConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await cleanup.execute(
                        f"DROP TABLE IF EXISTS `{schema}`.`{table}`"
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
        from pdip.integrator.connection.types.sql.connectors.mysql.async_mysql_connector import (
            AsyncMysqlConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        schema = "test_pdi"
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
            setup = AsyncMysqlConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f"CREATE TABLE `{schema}`.`{table}` (id INT)"
                )
                await setup.execute(
                    f"INSERT INTO `{schema}`.`{table}` VALUES (1)"
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

                verify = AsyncMysqlConnector(config=self.connection)
                await verify.connect()
                try:
                    post = await verify.fetch_count(
                        schema=schema, table=table
                    )
                    self.assertEqual(post, 0)
                finally:
                    await verify.disconnect()
            finally:
                cleanup = AsyncMysqlConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await cleanup.execute(
                        f"DROP TABLE IF EXISTS `{schema}`.`{table}`"
                    )
                finally:
                    await cleanup.disconnect()

        self._run(_drive())

    def test_async_target_adapter_clear_data_truncates_mysql_table(self):
        # End-to-end exercise of ADR-0032 follow-up (a-3) on the
        # MySQL target side: create a temp table, insert a row,
        # call ``AsyncSqlTargetAdapter.clear_data`` (which routes
        # to ``AsyncMysqlConnector.execute`` ``TRUNCATE TABLE`` with
        # backtick-quoted identifiers), verify the table is empty,
        # then drop the table.
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.target import (
            AsyncSqlTargetAdapter,
        )
        from pdip.integrator.connection.types.sql.connectors.mysql.async_mysql_connector import (
            AsyncMysqlConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        adapter = AsyncSqlTargetAdapter()
        schema = "test_pdi"
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
            setup = AsyncMysqlConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f"CREATE TABLE `{schema}`.`{table}` (id INT)"
                )
                await setup.execute(
                    f"INSERT INTO `{schema}`.`{table}` VALUES (1)"
                )
                pre = await setup.fetch_count(schema=schema, table=table)
                self.assertEqual(pre, 1)
            finally:
                await setup.disconnect()

            try:
                result = await adapter.clear_data(integration)
                self.assertEqual(result, 0)

                verify = AsyncMysqlConnector(config=self.connection)
                await verify.connect()
                try:
                    post = await verify.fetch_count(
                        schema=schema, table=table
                    )
                    self.assertEqual(post, 0)
                finally:
                    await verify.disconnect()
            finally:
                cleanup = AsyncMysqlConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await cleanup.execute(
                        f"DROP TABLE IF EXISTS `{schema}`.`{table}`"
                    )
                finally:
                    await cleanup.disconnect()

        self._run(_setup_then_clear_then_verify())
