"""Integration smoke test for the async MySQL connector wiring
(ADR-0032 §3 follow-up (a-2)).

Mirrors the asyncpg Postgres smoke test pattern against the
``tests/environments/mysql/`` fixture (MySQL 8.4 on
``localhost:3306``). Skips when ``aiomysql`` is not importable
(``pdip[async]`` not installed in the test environment).
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
