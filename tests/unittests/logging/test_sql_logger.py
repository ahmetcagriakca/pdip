"""Unit tests for ``pdip.logging.loggers.sql.sql_logger.SqlLogger``.

``SqlLogger`` persists log rows via a ``RepositoryProvider`` and, on
failure or when no ``LogData`` subclass is registered, delegates to
the injected ``ConsoleLogger``. We exercise both branches by mocking
the console logger at the boundary and patching ``RepositoryProvider``
and ``LogData.__subclasses__`` to steer through every arm.
"""

from logging import CRITICAL, DEBUG, ERROR, FATAL, INFO, NOTSET, WARNING
from unittest import TestCase
from unittest.mock import MagicMock, patch

from pdip.configuration.models.application import ApplicationConfig
from pdip.configuration.models.database import DatabaseConfig
from pdip.logging.loggers.sql.sql_logger import SqlLogger


def _make_logger(name="svc", hostname="host-a"):
    app = ApplicationConfig(name=name, hostname=hostname)
    db = DatabaseConfig(type="SQLITE", host="")
    console = MagicMock()
    return SqlLogger(application_config=app, database_config=db,
                     console_logger=console), console


class _FakeLogData:
    """Stand-in for a ``LogData`` subclass so ``log_to_db`` runs its
    happy path without needing a real database."""

    def __init__(self, TypeId=None, Content=None, LogDatetime=None,
                 JobId=None):
        self.TypeId = TypeId
        self.Content = Content
        self.LogDatetime = LogDatetime
        self.JobId = JobId


class SqlLoggerFallsBackToConsoleWhenRepositoryFails(TestCase):
    """The except+finally arms fire when ``RepositoryProvider`` blows
    up. We force that by patching it to a constructor that raises."""

    def test_error_logs_invoke_console_error_and_console_log(self):
        # Arrange
        sql_logger, console = _make_logger()

        # Act
        with patch(
            "pdip.logging.loggers.sql.sql_logger.LogData"
        ) as log_data_mock, patch(
            "pdip.logging.loggers.sql.sql_logger.RepositoryProvider",
            side_effect=RuntimeError("boom"),
        ):
            log_data_mock.__subclasses__ = MagicMock(
                return_value=[_FakeLogData]
            )
            sql_logger.error("plain", job_id=42)

        # Assert: except branch prefixes job_id and calls console.error.
        console.error.assert_called_once()
        err_msg = console.error.call_args[0][0]
        self.assertIn("42-plain", err_msg)
        self.assertIn("Sql logging getting error", err_msg)

        # finally branch calls console.log with the level. Note the
        # job_id gets prefixed twice because both the except and the
        # finally arms re-apply the prefix — asserted explicitly so
        # future refactors that fix the double-prefix flag here.
        console.log.assert_called_once()
        level, msg = console.log.call_args[0]
        self.assertEqual(level, ERROR)
        self.assertEqual(msg, "42-42-plain")

    def test_missing_job_id_does_not_prefix_message_in_finally(self):
        # Arrange
        sql_logger, console = _make_logger()

        # Act
        with patch(
            "pdip.logging.loggers.sql.sql_logger.LogData"
        ) as log_data_mock, patch(
            "pdip.logging.loggers.sql.sql_logger.RepositoryProvider",
            side_effect=RuntimeError("boom"),
        ):
            log_data_mock.__subclasses__ = MagicMock(
                return_value=[_FakeLogData]
            )
            sql_logger.info("hello")

        # Assert: no job-id prefix in either error or log line.
        console.error.assert_called_once()
        self.assertIn("hello", console.error.call_args[0][0])
        self.assertNotIn("None-", console.error.call_args[0][0])

        console.log.assert_called_once_with(INFO, "hello")


class SqlLoggerCommitsWhenRepositoryProviderSucceeds(TestCase):
    def test_happy_path_inserts_log_and_commits(self):
        # Arrange
        sql_logger, console = _make_logger()
        provider = MagicMock()
        repo = MagicMock()
        provider.get.return_value = repo

        # Act
        with patch(
            "pdip.logging.loggers.sql.sql_logger.LogData"
        ) as log_data_mock, patch(
            "pdip.logging.loggers.sql.sql_logger.RepositoryProvider",
            return_value=provider,
        ):
            log_data_mock.__subclasses__ = MagicMock(
                return_value=[_FakeLogData]
            )
            sql_logger.info("written", job_id=11)

        # Assert: the happy path inserts exactly once and commits.
        repo.insert.assert_called_once()
        inserted = repo.insert.call_args[0][0]
        self.assertEqual(inserted.TypeId, INFO)
        self.assertEqual(inserted.Content, "written")
        self.assertEqual(inserted.JobId, 11)
        provider.commit.assert_called_once()
        # console.error is skipped on the happy path.
        console.error.assert_not_called()
        # finally still mirrors the formatted message.
        console.log.assert_called_once_with(INFO, "11-written")


class SqlLoggerSkipsDbWhenNoSubclassRegistered(TestCase):
    def test_log_to_db_falls_through_to_console_log_directly(self):
        # Arrange
        sql_logger, console = _make_logger()

        # Act
        with patch(
            "pdip.logging.loggers.sql.sql_logger.LogData"
        ) as log_data_mock:
            log_data_mock.__subclasses__ = MagicMock(return_value=[])
            sql_logger.debug("empty-path", job_id=7)

        # Assert
        console.log.assert_called_once_with(DEBUG, "7-empty-path")
        console.error.assert_not_called()

    def test_log_to_db_without_job_id_in_else_branch(self):
        # Arrange
        sql_logger, console = _make_logger()

        # Act
        with patch(
            "pdip.logging.loggers.sql.sql_logger.LogData"
        ) as log_data_mock:
            log_data_mock.__subclasses__ = MagicMock(return_value=[])
            sql_logger.warning("raw")

        # Assert
        console.log.assert_called_once_with(WARNING, "raw")


class SqlLoggerExceptionWrapsTraceback(TestCase):
    def test_exception_with_message_prefixes_error_label(self):
        # Arrange
        sql_logger, console = _make_logger()

        # Act
        with patch(
            "pdip.logging.loggers.sql.sql_logger.LogData"
        ) as log_data_mock:
            log_data_mock.__subclasses__ = MagicMock(return_value=[])
            try:
                raise RuntimeError("kaboom")
            except RuntimeError as ex:
                sql_logger.exception(ex, message="while processing ")

        # Assert
        console.log.assert_called_once()
        level, msg = console.log.call_args[0]
        self.assertEqual(level, ERROR)
        self.assertIn("while processing ", msg)
        self.assertIn("Error:", msg)
        self.assertIn("kaboom", msg)

    def test_exception_without_message_uses_error_prefix(self):
        # Arrange
        sql_logger, console = _make_logger()

        # Act
        with patch(
            "pdip.logging.loggers.sql.sql_logger.LogData"
        ) as log_data_mock:
            log_data_mock.__subclasses__ = MagicMock(return_value=[])
            try:
                raise ValueError("oops")
            except ValueError as ex:
                sql_logger.exception(ex)

        # Assert
        console.log.assert_called_once()
        level, msg = console.log.call_args[0]
        self.assertEqual(level, ERROR)
        self.assertTrue(msg.startswith("Error:"))
        self.assertIn("oops", msg)


class SqlLoggerLevelMethodsDispatchToLogToDb(TestCase):
    def test_each_level_routes_through_console_with_right_level(self):
        # Arrange
        sql_logger, console = _make_logger()

        # Act
        with patch(
            "pdip.logging.loggers.sql.sql_logger.LogData"
        ) as log_data_mock:
            log_data_mock.__subclasses__ = MagicMock(return_value=[])
            sql_logger.critical("c", 1)
            sql_logger.fatal("f")
            sql_logger.warning("w")
            sql_logger.info("i")
            sql_logger.debug("d")
            sql_logger.log("n")

        # Assert
        observed_levels = [c.args[0] for c in console.log.call_args_list]
        self.assertEqual(
            observed_levels,
            [CRITICAL, FATAL, WARNING, INFO, DEBUG, NOTSET],
        )


class SqlLoggerBuildsCommentWhenConfigIsSparse(TestCase):
    def test_missing_name_and_hostname_still_produces_console_log(self):
        # Arrange
        app = ApplicationConfig(name=None, hostname=None)
        db = DatabaseConfig(type="SQLITE", host="")
        console = MagicMock()
        logger = SqlLogger(application_config=app, database_config=db,
                           console_logger=console)

        # Act
        with patch(
            "pdip.logging.loggers.sql.sql_logger.LogData"
        ) as log_data_mock:
            log_data_mock.__subclasses__ = MagicMock(return_value=[])
            logger.info("no-names")

        # Assert
        console.log.assert_called_once_with(INFO, "no-names")
