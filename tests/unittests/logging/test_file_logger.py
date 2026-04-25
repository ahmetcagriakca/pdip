"""Unit tests for ``pdip.logging.loggers.file.file_logger.FileLogger``.

The FileLogger contract is that every level method is callable
without raising. Assert it explicitly per ADR-0026 A.1 rather than
relying on the absence of an exception. These tests also pin down
the ``exception`` formatting branches and the destructor.
"""

import logging
from unittest import TestCase
from unittest.mock import MagicMock

from pdip.logging.loggers.file import FileLogger


class FileLoggerAcceptsEveryLevel(TestCase):
    def test_each_level_returns_none_and_does_not_raise(self):
        file_logger = FileLogger()
        for level, message in [
            ("debug", "debug"),
            ("info", "info"),
            ("warning", "warning"),
            ("error", "error"),
            ("fatal", "fatal"),
        ]:
            self.assertIsNone(getattr(file_logger, level)(message))


class FileLoggerExceptionIncludesTraceback(TestCase):
    def setUp(self):
        self.file_logger = FileLogger()
        self.file_logger.logger = MagicMock(spec=logging.Logger)

    def test_exception_without_message_formats_error_traceback(self):
        err = RuntimeError("boom")

        self.file_logger.exception(err)

        self.file_logger.logger.error.assert_called_once()
        logged = self.file_logger.logger.error.call_args.args[0]
        self.assertIn("Error:", logged)
        self.assertIn("boom", logged)

    def test_exception_with_message_prefixes_caller_message(self):
        err = ValueError("bad-value")

        self.file_logger.exception(err, message="context: ")

        logged = self.file_logger.logger.error.call_args.args[0]
        self.assertTrue(logged.startswith("context: "))
        self.assertIn("bad-value", logged)


class FileLoggerDelegatesLevelMethodsToLogger(TestCase):
    def setUp(self):
        self.file_logger = FileLogger()
        self.file_logger.logger = MagicMock(spec=logging.Logger)

    def test_critical_delegates_to_logger_critical(self):
        self.file_logger.critical("crit")
        self.file_logger.logger.critical.assert_called_once_with("crit")

    def test_log_delegates_level_and_message(self):
        self.file_logger.log(20, "info-line")
        self.file_logger.logger.log.assert_called_once_with(20, "info-line")


class FileLoggerDestructorRemovesHandler(TestCase):
    def test_del_removes_handler_from_underlying_logger(self):
        file_logger = FileLogger()
        file_logger.logger = MagicMock(spec=logging.Logger)
        handler_sentinel = object()
        file_logger.file_handler = handler_sentinel

        file_logger.__del__()

        file_logger.logger.removeHandler.assert_called_once_with(
            handler_sentinel
        )
