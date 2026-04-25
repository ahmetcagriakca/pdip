"""Integration smoke test for the async Oracle connector wiring
(ADR-0032 §3 follow-up (a-2)).

Mirrors the asyncpg Postgres smoke pattern against the
``tests/environments/oracle/`` fixture (Oracle XE 21c on
``localhost:1521``). Uses ``oracledb.connect_async`` from the same
``oracledb`` package the sync Oracle path uses (ADR-0021), so this
test only skips if the package itself is missing.
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
