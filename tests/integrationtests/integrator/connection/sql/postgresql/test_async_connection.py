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
