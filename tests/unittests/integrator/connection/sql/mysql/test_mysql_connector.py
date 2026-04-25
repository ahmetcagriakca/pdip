"""Unit tests for the MySQL connector.

Exercises the connector's shape with ``mysql.connector`` mocked so CI
does not need the native driver (and to prove the code uses only the
call signatures that survived the 8.x → 9.x bump). The real driver is
installed behind the ``integrator`` extra; integration tests live
under ``tests/integrationtests/`` and require a running MySQL.
"""

import sys
import types
from unittest import TestCase
from unittest.mock import MagicMock, patch


def _install_mysql_stub():
    """Stub ``mysql.connector`` in ``sys.modules`` before the connector
    is imported. Returns the originals so callers can restore them."""

    saved = {
        name: sys.modules.get(name)
        for name in ("mysql", "mysql.connector")
    }

    pkg = types.ModuleType("mysql")
    pkg.__path__ = []
    sub = types.ModuleType("mysql.connector")
    sub.connect = MagicMock(name="connect")
    sub.connect.return_value.cursor.return_value = MagicMock()
    pkg.connector = sub
    sys.modules["mysql"] = pkg
    sys.modules["mysql.connector"] = sub
    return saved, sub


def _restore(saved):
    for name, original in saved.items():
        if original is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = original


# Install stub, load the connector, then restore sys.modules so other
# tests (or doctest discovery) see the original state.
_saved, _mysql_connector = _install_mysql_stub()
try:
    from pdip.integrator.connection.types.sql.connectors.mysql import (  # noqa: E402
        MysqlConnector,
    )
    from pdip.integrator.connection.types.sql.connectors.mysql import (  # noqa: E402
        mysql_connector as _mc_module,
    )
finally:
    _restore(_saved)


class _Stub:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def _build_config():
    return _Stub(
        Database="appdb",
        Server=_Stub(Host="db", Port=3306),
        BasicAuthentication=_Stub(User="scott", Password="tiger"),
    )


class MysqlConnectorUsesDbApiCallShape(TestCase):
    def setUp(self):
        self.fake_module = MagicMock()
        self.fake_module.connector.connect.return_value = MagicMock()
        # Patch the module-level reference the connector captured.
        self._patch = patch.object(_mc_module, "mysql", self.fake_module)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()

    def test_connect_uses_expected_keyword_arguments(self):
        connector = MysqlConnector(_build_config())
        connector.connect()
        self.fake_module.connector.connect.assert_called_once_with(
            user="scott",
            password="tiger",
            database="appdb",
            host="db",
            port=3306,
        )

    def test_disconnect_closes_cursor_and_connection(self):
        connector = MysqlConnector(_build_config())
        connector.connect()
        cursor = connector.cursor
        connection = connector.connection

        connector.disconnect()

        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_disconnect_is_safe_before_connect(self):
        connector = MysqlConnector(_build_config())

        connector.disconnect()

        # After a disconnect with no prior connect, the connector's
        # state stays unset — no phantom connection or cursor appears.
        self.assertIsNone(connector.connection)
        self.assertIsNone(connector.cursor)


class MysqlConnectorBuildsSqlAlchemyUrl(TestCase):
    def test_get_engine_connection_url_has_mysql_scheme(self):
        connector = MysqlConnector(_build_config())
        url = connector.get_engine_connection_url()
        # SQLAlchemy's URL.render_as_string masks the password unless
        # hide_password is False.
        self.assertIn("mysql://", str(url))
        self.assertIn("scott", str(url))
        self.assertEqual(url.host, "db")
        self.assertEqual(url.port, 3306)
        self.assertEqual(url.database, "appdb")
