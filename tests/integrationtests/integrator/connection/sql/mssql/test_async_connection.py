"""Integration smoke test for the async MSSQL connector wiring
(ADR-0032 §3 follow-up (a-2)).

Mirrors the asyncpg Postgres smoke pattern against the
``tests/environments/mssql/`` fixture (SQL Server 2022). Skips
when ``aioodbc`` is not importable (``pdip[async]`` not installed
in the test environment) — note ``aioodbc`` itself wraps ``pyodbc``
which already requires a host-level ODBC Driver 18 install per the
sync MSSQL integration tests.
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
