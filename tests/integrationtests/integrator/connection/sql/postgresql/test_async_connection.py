"""Integration smoke test for the async Postgres connector +
adapter wiring (ADR-0032 §3 follow-up (a)).

Mirrors the sync ``test_connection.py`` smoke layout against the
``tests/environments/postgresql/`` Docker fixture (Postgres 16 on
``localhost:5434``). The test is skipped automatically when:

- ``asyncpg`` is not importable (``pdip[async]`` extra not
  installed in the test environment), or
- the fixture's Postgres is not reachable (covered by the
  ``ConnectionRefusedError`` / ``OSError`` raised from
  ``asyncpg.connect``; tests under ``tests/integrationtests/`` are
  CI-gated by the nightly job per ADR-0029, not the per-PR unit
  matrix).
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


def _asyncpg_available() -> bool:
    try:
        import asyncpg  # noqa: F401 — presence check only
    except ImportError:
        return False
    return True


@unittest.skipUnless(
    _asyncpg_available(),
    "pdip[async] not installed — asyncpg import unavailable",
)
class TestAsyncPostgresqlConnection(TestCase):
    def setUp(self):
        self.connection = SqlConnectionConfiguration(
            Name='TestAsyncConnection',
            ConnectionType=ConnectionTypes.Sql,
            ConnectorType=ConnectorTypes.POSTGRESQL,
            Server=ConnectionServer(Host='localhost', Port='5434'),
            Database='test_pdi',
            BasicAuthentication=ConnectionBasicAuthentication(
                User='pdi', Password='pdi!123456'
            ),
        )

    def _run(self, coro):
        return asyncio.new_event_loop().run_until_complete(coro)

    def test_async_connector_connect_then_disconnect(self):
        from pdip.integrator.connection.types.sql.connectors.postgresql.async_postgresql_connector import (  # noqa: E501
            AsyncPostgresqlConnector,
        )
        connector = AsyncPostgresqlConnector(config=self.connection)

        async def _drive():
            await connector.connect()
            try:
                self.assertIsNotNone(connector.connection)
            finally:
                await connector.disconnect()
            self.assertIsNone(connector.connection)

        self._run(_drive())

    def test_async_connector_fetch_count_against_information_schema(self):
        # ``information_schema.tables`` always exists on Postgres and
        # returns a deterministic row count for the smoke test —
        # avoids depending on test fixture state.
        from pdip.integrator.connection.types.sql.connectors.postgresql.async_postgresql_connector import (  # noqa: E501
            AsyncPostgresqlConnector,
        )
        connector = AsyncPostgresqlConnector(config=self.connection)

        async def _drive():
            await connector.connect()
            try:
                count = await connector.fetch_count(
                    schema="information_schema", table="tables"
                )
                self.assertGreater(count, 0)
            finally:
                await connector.disconnect()

        self._run(_drive())

    def test_async_source_adapter_get_source_data_count_returns_int(self):
        # Drives the full chain: AsyncSqlSourceAdapter →
        # AsyncPostgresqlConnector → asyncpg. Uses an
        # ``IntegrationBase`` whose ``SourceConnections`` points at a
        # known schema/table.
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
                    ObjectName="tables",
                ),
            ),
        )

        async def _drive():
            count = await adapter.get_source_data_count(integration)
            self.assertGreater(count, 0)

        self._run(_drive())

    def test_async_source_adapter_get_iterator_chunks_into_batches(self):
        # Drives ``AsyncSqlSourceAdapter.get_iterator`` against a
        # known-sized source table — verifies the chunking
        # math (``rows[i:i+limit]``) matches the documented
        # batch-iteration contract.
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.source import (
            AsyncSqlSourceAdapter,
        )
        from pdip.integrator.connection.types.sql.connectors.postgresql.async_postgresql_connector import (  # noqa: E501
            AsyncPostgresqlConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        schema = "public"
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
            setup = AsyncPostgresqlConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f'CREATE TABLE "{schema}"."{table}" (id INT)'
                )
                # 7 rows + limit=3 → batches [3, 3, 1].
                for i in range(1, 8):
                    await setup.execute(
                        f'INSERT INTO "{schema}"."{table}" '
                        f'VALUES ({i})'
                    )
            finally:
                await setup.disconnect()

            try:
                batches = await adapter.get_iterator(
                    integration=integration, limit=3
                )
                self.assertEqual([len(b) for b in batches], [3, 3, 1])
            finally:
                cleanup = AsyncPostgresqlConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await cleanup.execute(
                        f'DROP TABLE IF EXISTS "{schema}"."{table}"'
                    )
                finally:
                    await cleanup.disconnect()

        self._run(_drive())

    def test_async_source_adapter_get_source_data_with_paging(self):
        # ``LIMIT/OFFSET`` form against information_schema, which
        # has a stable ordering guarantee for our purposes (no
        # writes between calls).
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
                    ObjectName="tables",
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
        # table, then drop it.
        from pdip.integrator.connection.domain.base import (
            ConnectionColumnBase,
        )
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.target import (
            AsyncSqlTargetAdapter,
        )
        from pdip.integrator.connection.types.sql.connectors.postgresql.async_postgresql_connector import (  # noqa: E501
            AsyncPostgresqlConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        schema = "public"
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
            setup = AsyncPostgresqlConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f'CREATE TABLE "{schema}"."{table}" '
                    f'(id INT, name VARCHAR(50))'
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

                verify = AsyncPostgresqlConnector(config=self.connection)
                await verify.connect()
                try:
                    count = await verify.fetch_count(
                        schema=schema, table=table
                    )
                    self.assertEqual(count, 2)
                finally:
                    await verify.disconnect()
            finally:
                cleanup = AsyncPostgresqlConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await cleanup.execute(
                        f'DROP TABLE IF EXISTS "{schema}"."{table}"'
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
        from pdip.integrator.connection.types.sql.connectors.postgresql.async_postgresql_connector import (  # noqa: E501
            AsyncPostgresqlConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        schema = "public"
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
            setup = AsyncPostgresqlConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f'CREATE TABLE "{schema}"."{table}" (id INT)'
                )
                await setup.execute(
                    f'INSERT INTO "{schema}"."{table}" VALUES (1)'
                )
            finally:
                await setup.disconnect()

            try:
                # Without flag: returns 0, no truncate.
                noop_result = await adapter.do_target_operation(
                    integration=_make_integration(False)
                )
                self.assertEqual(noop_result, 0)
                # With flag: truncates and returns 0 (Postgres
                # TRUNCATE has no row count).
                truncate_result = await adapter.do_target_operation(
                    integration=_make_integration(True)
                )
                self.assertEqual(truncate_result, 0)

                verify = AsyncPostgresqlConnector(config=self.connection)
                await verify.connect()
                try:
                    post = await verify.fetch_count(
                        schema=schema, table=table
                    )
                    self.assertEqual(post, 0)
                finally:
                    await verify.disconnect()
            finally:
                cleanup = AsyncPostgresqlConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await cleanup.execute(
                        f'DROP TABLE IF EXISTS "{schema}"."{table}"'
                    )
                finally:
                    await cleanup.disconnect()

        self._run(_drive())

    def test_async_target_adapter_clear_data_truncates_postgres_table(self):
        # End-to-end exercise of ADR-0032 follow-up (a-3 partial)
        # on the target side: create a temp table, insert a row,
        # call ``AsyncSqlTargetAdapter.clear_data`` (which routes
        # to ``AsyncPostgresqlConnector.execute`` ``TRUNCATE TABLE``),
        # verify the table is empty, then drop the table.
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.target import (
            AsyncSqlTargetAdapter,
        )
        from pdip.integrator.connection.types.sql.connectors.postgresql.async_postgresql_connector import (  # noqa: E501
            AsyncPostgresqlConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        adapter = AsyncSqlTargetAdapter()
        schema = "public"
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
            # Setup: create + populate via a separate connector
            # instance so the test isolates the clear_data path.
            setup = AsyncPostgresqlConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f'CREATE TABLE "{schema}"."{table}" (id INT)'
                )
                await setup.execute(
                    f'INSERT INTO "{schema}"."{table}" VALUES (1)'
                )
                pre = await setup.fetch_count(schema=schema, table=table)
                self.assertEqual(pre, 1)
            finally:
                await setup.disconnect()

            # Act: clear_data through the target adapter.
            try:
                result = await adapter.clear_data(integration)
                self.assertEqual(result, 0)

                # Assert: table is empty.
                verify = AsyncPostgresqlConnector(config=self.connection)
                await verify.connect()
                try:
                    post = await verify.fetch_count(
                        schema=schema, table=table
                    )
                    self.assertEqual(post, 0)
                finally:
                    await verify.disconnect()
            finally:
                # Cleanup: drop the test table regardless of outcome.
                cleanup = AsyncPostgresqlConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await cleanup.execute(
                        f'DROP TABLE IF EXISTS "{schema}"."{table}"'
                    )
                finally:
                    await cleanup.disconnect()

        self._run(_setup_then_clear_then_verify())
