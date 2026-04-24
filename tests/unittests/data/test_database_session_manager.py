"""Unit tests for ``pdip.data.base.database_session_manager.DatabaseSessionManager``.

The session manager owns engine/session construction. These tests
exercise two connect() branches that the integration suites do not
reach:

* connection-string auto-derivation when the config leaves it blank,
* the non-SQLITE engine-construction branch (uses ``NullPool``).

``sqlalchemy.create_engine`` is mocked at the module boundary so no
real database engine is started.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from pdip.configuration.models.database import DatabaseConfig
from pdip.data.base import database_session_manager as dsm_module


class DatabaseSessionManagerConnectBranches(TestCase):
    def test_blank_connection_string_is_auto_derived_from_config(self):
        # Arrange
        config = DatabaseConfig(
            type="SQLITE",
            connection_string="",
            host="auto.db",
        )

        with patch.object(dsm_module, "create_engine") as create_engine, \
             patch.object(dsm_module, "sessionmaker") as sessionmaker:
            create_engine.return_value = MagicMock(name="engine")
            sessionmaker.return_value = MagicMock(
                return_value=MagicMock(name="session")
            )

            # Act
            manager = dsm_module.DatabaseSessionManager(database_config=config)

        # Assert — the blank string was replaced and then passed to
        # create_engine as the first positional argument.
        self.assertNotEqual(manager.database_config.connection_string, "")
        (dsn_arg,), _ = create_engine.call_args
        self.assertEqual(dsn_arg, manager.database_config.connection_string)

    def test_non_sqlite_engine_uses_null_pool_and_application_name(self):
        # Arrange
        config = DatabaseConfig(
            type="POSTGRESQL",
            connection_string="postgresql://user:pass@db:5432/app",
            application_name="pdip-tests",
        )

        with patch.object(dsm_module, "create_engine") as create_engine, \
             patch.object(dsm_module, "sessionmaker") as sessionmaker:
            create_engine.return_value = MagicMock(name="engine")
            sessionmaker.return_value = MagicMock(
                return_value=MagicMock(name="session")
            )

            # Act
            dsm_module.DatabaseSessionManager(database_config=config)

        # Assert — the non-SQLITE branch forwards NullPool + application_name.
        _, kwargs = create_engine.call_args
        self.assertIs(kwargs["poolclass"], dsm_module.pool.NullPool)
        self.assertTrue(kwargs["pool_pre_ping"])
        self.assertEqual(
            kwargs["connect_args"], {"application_name": "pdip-tests"}
        )
