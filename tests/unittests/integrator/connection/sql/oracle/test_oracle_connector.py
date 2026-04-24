"""Unit tests for the Oracle connector after the ``python-oracledb``
migration (see ADR-0021).

The integration tests live under ``tests/integrationtests/`` and need a
real Oracle server. Here we mock the ``oracledb`` driver so CI can
exercise the connector's shape — URL composition, connect arguments,
SQLAlchemy scheme, disconnect semantics — on every Python version.
"""

import sys
import types
from unittest import TestCase
from unittest.mock import MagicMock, patch


def _install_oracledb_stub():
    """Install a fake ``oracledb`` module in ``sys.modules`` **before**
    the connector module is imported, so the connector's top-level
    ``import oracledb`` resolves to the stub."""

    module = types.ModuleType("oracledb")
    module.makedsn = MagicMock(return_value="MOCK_DSN")
    module.connect = MagicMock()
    module.connect.return_value.cursor.return_value = MagicMock()
    sys.modules["oracledb"] = module
    return module


# Install the stub eagerly at import time so the first import of the
# connector module anywhere in the test suite sees the stub.
_STUB = _install_oracledb_stub()

# Import after the stub is installed.
from pdip.integrator.connection.types.sql.connectors.oracle import (  # noqa: E402
    OracleConnector,
)
from pdip.integrator.connection.types.sql.connectors.oracle import (  # noqa: E402
    oracle_connector as _connector_module,
)


class _Stub:
    """Attribute bag used to stand in for configuration dataclasses so
    tests do not pull the whole integrator domain."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def _build_config(sid=None, service_name=None, host="db", port=1521,
                  user="scott", password="tiger"):
    return _Stub(
        Sid=sid,
        ServiceName=service_name,
        Server=_Stub(Host=host, Port=port),
        BasicAuthentication=_Stub(User=user, Password=password),
    )


class OracleConnectorUsesOracledb(TestCase):
    def setUp(self):
        self.oracledb = MagicMock()
        self.oracledb.makedsn.return_value = "MOCK_DSN"
        self.oracledb.connect.return_value = MagicMock()
        # Point the connector's module-level name at a fresh mock for
        # this test, avoiding cross-test interference through the
        # sys.modules stub.
        self._patch = patch.object(_connector_module, "oracledb", self.oracledb)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()

    def test_connect_prefers_sid_when_provided(self):
        connector = OracleConnector(_build_config(sid="ORCL", service_name="svc.local"))

        connector.connect()

        self.oracledb.makedsn.assert_called_once_with(
            "db", 1521, service_name="ORCL"
        )
        self.oracledb.connect.assert_called_once_with(
            user="scott", password="tiger", dsn="MOCK_DSN"
        )

    def test_connect_falls_back_to_service_name_when_sid_missing(self):
        connector = OracleConnector(_build_config(sid=None, service_name="svc.local"))

        connector.connect()

        self.oracledb.makedsn.assert_called_once_with(
            "db", 1521, service_name="svc.local"
        )

    def test_disconnect_closes_cursor_and_connection(self):
        connector = OracleConnector(_build_config(sid="ORCL"))
        connector.connect()
        cursor = connector.cursor
        connection = connector.connection

        connector.disconnect()

        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_disconnect_is_safe_when_never_connected(self):
        connector = OracleConnector(_build_config(sid="ORCL"))
        connector.disconnect()  # must not raise


class OracleConnectorBuildsSqlAlchemyUrl(TestCase):
    def test_sid_url_uses_oracledb_scheme(self):
        connector = OracleConnector(_build_config(sid="ORCL"))
        self.assertEqual(
            connector.get_engine_connection_url(),
            "oracle+oracledb://scott:tiger@db:1521/ORCL",
        )

    def test_service_name_url_uses_oracledb_scheme(self):
        connector = OracleConnector(_build_config(sid=None, service_name="svc.local"))
        self.assertEqual(
            connector.get_engine_connection_url(),
            "oracle+oracledb://scott:tiger@db:1521/svc.local",
        )
