"""Integration smoke test for the async Oracle connector + adapter
wiring (ADR-0032 §3 follow-up (a-2 / a-3)).

Mirrors the asyncpg Postgres smoke pattern against the
``tests/environments/oracle/`` fixture (Oracle XE 21c on
``localhost:1521``). Uses ``oracledb.connect_async`` from the
same ``oracledb`` package the sync Oracle path uses (ADR-0021),
so this test only skips if the package itself is missing.

The adapter-level cases (``get_source_data_count`` /
``get_iterator`` / ``get_source_data_with_paging`` /
``write_data`` / ``do_target_operation`` / ``clear_data``)
exercise the dialect helper's Oracle form: double-quoted
upper-case identifiers, ``:N`` placeholders, and the ANSI
``OFFSET ... FETCH NEXT`` paging clause (which requires the
source query to carry an ``ORDER BY`` for a deterministic page).

Oracle XE 21c does not support ``DROP TABLE IF EXISTS``; the
cleanup blocks below swallow ORA-00942 ("table or view does not
exist") so a failed setup never masks the original assertion.
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


def _oracledb_async_available() -> bool:
    try:
        import oracledb  # noqa: F401 — presence check only
    except ImportError:
        return False
    return hasattr(oracledb, "connect_async")


async def _drop_if_exists(connector, schema, table):
    """Oracle XE 21c lacks ``DROP TABLE IF EXISTS``; swallow
    ORA-00942 so cleanup never re-raises when the setup half
    failed before the table was created."""
    try:
        await connector.execute(
            f'DROP TABLE "{schema}"."{table}"'
        )
    except Exception as exc:  # pragma: no cover — runtime-only path
        if "ORA-00942" not in str(exc):
            raise


@unittest.skipUnless(
    _oracledb_async_available(),
    "oracledb (>= async-API era) is not installed",
)
class TestAsyncOracleConnection(TestCase):
    def setUp(self):
        self.connection = SqlConnectionConfiguration(
            Name='TestAsyncOracleConnection',
            ConnectionType=ConnectionTypes.Sql,
            ConnectorType=ConnectorTypes.ORACLE,
            Server=ConnectionServer(Host='localhost', Port='1521'),
            Database='XEPDB1',
            BasicAuthentication=ConnectionBasicAuthentication(
                User='pdi', Password='pdi!123456'
            ),
        )

    def _run(self, coro):
        return asyncio.new_event_loop().run_until_complete(coro)

    def test_async_connector_connect_then_disconnect(self):
        from pdip.integrator.connection.types.sql.connectors.oracle.async_oracle_connector import (
            AsyncOracleConnector,
        )
        connector = AsyncOracleConnector(config=self.connection)

        async def _drive():
            await connector.connect()
            try:
                self.assertIsNotNone(connector.connection)
            finally:
                await connector.disconnect()
            self.assertIsNone(connector.connection)

        self._run(_drive())

    def test_async_connector_fetch_count_against_dual(self):
        # ``dual`` is Oracle's canonical 1-row pseudo-table; using
        # it avoids depending on user schema state.
        from pdip.integrator.connection.types.sql.connectors.oracle.async_oracle_connector import (
            AsyncOracleConnector,
        )
        connector = AsyncOracleConnector(config=self.connection)

        async def _drive():
            await connector.connect()
            try:
                count = await connector.fetch_count(
                    schema="SYS", table="DUAL"
                )
                self.assertEqual(count, 1)
            finally:
                await connector.disconnect()

        self._run(_drive())

    def test_async_source_adapter_get_source_data_count_returns_dual_one(self):
        # Drives the full chain: AsyncSqlSourceAdapter →
        # AsyncOracleConnector → oracledb. ``SYS.DUAL`` always has
        # exactly one row.
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
                    Schema="SYS",
                    ObjectName="DUAL",
                ),
            ),
        )

        async def _drive():
            count = await adapter.get_source_data_count(integration)
            self.assertEqual(count, 1)

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
        from pdip.integrator.connection.types.sql.connectors.oracle.async_oracle_connector import (
            AsyncOracleConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        schema = "PDI"
        table = "TEST_ASYNC_ITERATOR_PAGES"
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
            setup = AsyncOracleConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f'CREATE TABLE "{schema}"."{table}" '
                    f'("ID" NUMBER)'
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
                cleanup = AsyncOracleConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await _drop_if_exists(cleanup, schema, table)
                finally:
                    await cleanup.disconnect()

        self._run(_drive())

    def test_async_source_adapter_get_source_data_with_paging(self):
        # Oracle 12c+ ``OFFSET ... FETCH NEXT`` paging requires
        # the base query to carry an ``ORDER BY``. We supply one
        # via the descriptor's explicit ``Sql.Query`` so the
        # adapter's ``_select_query_for`` returns it verbatim.
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.source import (
            AsyncSqlSourceAdapter,
        )
        from pdip.integrator.connection.types.sql.connectors.oracle.async_oracle_connector import (
            AsyncOracleConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        schema = "PDI"
        table = "TEST_ASYNC_PAGING"
        adapter = AsyncSqlSourceAdapter()
        integration = IntegrationBase(
            SourceConnections=IntegrationConnectionBase(
                ConnectionType=ConnectionTypes.Sql,
                Sql=ConnectionSqlBase(
                    Connection=self.connection,
                    Schema=schema,
                    ObjectName=table,
                    Query=(
                        f'SELECT "ID" FROM "{schema}"."{table}" '
                        f'ORDER BY "ID"'
                    ),
                ),
            ),
        )

        async def _drive():
            setup = AsyncOracleConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f'CREATE TABLE "{schema}"."{table}" '
                    f'("ID" NUMBER)'
                )
                for i in range(1, 11):
                    await setup.execute(
                        f'INSERT INTO "{schema}"."{table}" '
                        f'VALUES ({i})'
                    )
            finally:
                await setup.disconnect()

            try:
                page = await adapter.get_source_data_with_paging(
                    integration=integration, start=2, end=7
                )
                self.assertEqual(len(page), 5)
                # Deterministic order guarantee from ORDER BY ID.
                self.assertEqual(
                    [row["ID"] for row in page], [3, 4, 5, 6, 7]
                )
            finally:
                cleanup = AsyncOracleConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await _drop_if_exists(cleanup, schema, table)
                finally:
                    await cleanup.disconnect()

        self._run(_drive())

    def test_async_target_adapter_write_data_inserts_rows(self):
        # End-to-end ``write_data`` exercise: create a temp table,
        # call ``AsyncSqlTargetAdapter.write_data`` with two
        # dict-shaped rows, verify both landed by counting the
        # table, then drop it. Exercises the Oracle placeholder
        # ladder (``:1, :2``) and double-quoted upper-case
        # identifiers. Source-row keys must match Oracle's stored
        # column case (uppercase) for the dict-extract path to hit.
        from pdip.integrator.connection.domain.base import (
            ConnectionColumnBase,
        )
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.target import (
            AsyncSqlTargetAdapter,
        )
        from pdip.integrator.connection.types.sql.connectors.oracle.async_oracle_connector import (
            AsyncOracleConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        schema = "PDI"
        table = "TEST_ASYNC_WRITE_DATA"
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
                    ConnectionColumnBase(Name="ID", Type="NUMBER"),
                    ConnectionColumnBase(
                        Name="NAME", Type="VARCHAR2(50)"
                    ),
                ],
            ),
        )

        async def _drive():
            setup = AsyncOracleConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f'CREATE TABLE "{schema}"."{table}" '
                    f'("ID" NUMBER, "NAME" VARCHAR2(50))'
                )
            finally:
                await setup.disconnect()

            try:
                rows_written = await adapter.write_data(
                    integration=integration,
                    source_data=[
                        {"ID": 1, "NAME": "alice"},
                        {"ID": 2, "NAME": "bob"},
                    ],
                )
                self.assertEqual(rows_written, 2)

                verify = AsyncOracleConnector(config=self.connection)
                await verify.connect()
                try:
                    count = await verify.fetch_count(
                        schema=schema, table=table
                    )
                    self.assertEqual(count, 2)
                finally:
                    await verify.disconnect()
            finally:
                cleanup = AsyncOracleConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await _drop_if_exists(cleanup, schema, table)
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
        from pdip.integrator.connection.types.sql.connectors.oracle.async_oracle_connector import (
            AsyncOracleConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        schema = "PDI"
        table = "TEST_ASYNC_DO_TARGET_OP"
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
            setup = AsyncOracleConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f'CREATE TABLE "{schema}"."{table}" '
                    f'("ID" NUMBER)'
                )
                await setup.execute(
                    f'INSERT INTO "{schema}"."{table}" VALUES (1)'
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

                verify = AsyncOracleConnector(config=self.connection)
                await verify.connect()
                try:
                    post = await verify.fetch_count(
                        schema=schema, table=table
                    )
                    self.assertEqual(post, 0)
                finally:
                    await verify.disconnect()
            finally:
                cleanup = AsyncOracleConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await _drop_if_exists(cleanup, schema, table)
                finally:
                    await cleanup.disconnect()

        self._run(_drive())

    def test_async_target_adapter_clear_data_truncates_oracle_table(self):
        # End-to-end exercise of ADR-0032 follow-up (a-3) on the
        # Oracle target side: create a temp table, insert a row,
        # call ``AsyncSqlTargetAdapter.clear_data`` (which routes
        # to ``AsyncOracleConnector.execute`` ``TRUNCATE TABLE``
        # with double-quoted upper-case identifiers), verify the
        # table is empty, then drop the table.
        from pdip.integrator.connection.domain.types.sql.base import (
            ConnectionSqlBase,
        )
        from pdip.integrator.connection.types.sql.adapters.target import (
            AsyncSqlTargetAdapter,
        )
        from pdip.integrator.connection.types.sql.connectors.oracle.async_oracle_connector import (
            AsyncOracleConnector,
        )
        from pdip.integrator.integration.domain.base import (
            IntegrationBase,
            IntegrationConnectionBase,
        )

        adapter = AsyncSqlTargetAdapter()
        schema = "PDI"
        table = "TEST_ASYNC_CLEAR_DATA"
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
            setup = AsyncOracleConnector(config=self.connection)
            await setup.connect()
            try:
                await setup.execute(
                    f'CREATE TABLE "{schema}"."{table}" '
                    f'("ID" NUMBER)'
                )
                await setup.execute(
                    f'INSERT INTO "{schema}"."{table}" VALUES (1)'
                )
                pre = await setup.fetch_count(schema=schema, table=table)
                self.assertEqual(pre, 1)
            finally:
                await setup.disconnect()

            try:
                result = await adapter.clear_data(integration)
                self.assertEqual(result, 0)

                verify = AsyncOracleConnector(config=self.connection)
                await verify.connect()
                try:
                    post = await verify.fetch_count(
                        schema=schema, table=table
                    )
                    self.assertEqual(post, 0)
                finally:
                    await verify.disconnect()
            finally:
                cleanup = AsyncOracleConnector(config=self.connection)
                await cleanup.connect()
                try:
                    await _drop_if_exists(cleanup, schema, table)
                finally:
                    await cleanup.disconnect()

        self._run(_setup_then_clear_then_verify())
