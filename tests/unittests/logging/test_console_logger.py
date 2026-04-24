"""Unit tests for ``pdip.logging.loggers.console.console_logger.ConsoleLogger``.

The ``basic_app*`` suites exercise ``info``/``debug`` indirectly. This
module pins down the branches those suites don't reach: ``exception``
with/without an explicit message, plus ``critical``, ``fatal``, and
``error`` — each of which must delegate straight to the underlying
``logging.Logger``.

Per ADR-0026 A.1 every test asserts concrete behaviour.
"""

import logging
from unittest import TestCase
from unittest.mock import MagicMock, patch

from pdip.logging.loggers.console.console_logger import ConsoleLogger


class ConsoleLoggerExceptionIncludesTraceback(TestCase):
    def setUp(self):
        # Arrange — fresh instance with a stubbed underlying logger so
        # we can assert the exact call made.
        self.console_logger = ConsoleLogger()
        self.console_logger.logger = MagicMock(spec=logging.Logger)

    def test_exception_without_message_formats_error_traceback(self):
        err = RuntimeError("boom")

        self.console_logger.exception(err)

        self.console_logger.logger.error.assert_called_once()
        logged = self.console_logger.logger.error.call_args.args[0]
        self.assertIn("Error:", logged)
        self.assertIn("boom", logged)

    def test_exception_with_message_prefixes_caller_message(self):
        err = ValueError("bad-value")

        self.console_logger.exception(err, message="context: ")

        logged = self.console_logger.logger.error.call_args.args[0]
        self.assertTrue(logged.startswith("context: "))
        self.assertIn("bad-value", logged)


class ConsoleLoggerDelegatesLevelMethodsToLogger(TestCase):
    def setUp(self):
        self.console_logger = ConsoleLogger()
        self.console_logger.logger = MagicMock(spec=logging.Logger)

    def test_critical_delegates_to_logger_critical(self):
        self.console_logger.critical("crit")
        self.console_logger.logger.critical.assert_called_once_with("crit")

    def test_fatal_delegates_to_logger_fatal(self):
        self.console_logger.fatal("fatal-msg")
        self.console_logger.logger.fatal.assert_called_once_with("fatal-msg")

    def test_error_delegates_to_logger_error(self):
        self.console_logger.error("err")
        self.console_logger.logger.error.assert_called_once_with("err")

    def test_warning_delegates_to_logger_warning(self):
        self.console_logger.warning("warn")
        self.console_logger.logger.warning.assert_called_once_with("warn")


class ConsoleLoggerLogInitIsIdempotent(TestCase):
    def test_log_init_skips_when_handlers_already_present(self):
        # Arrange — first construction installs a handler on the
        # shared 'pdip.console_logger' logger; a second construction
        # must keep the same handler count (the ``if not
        # self.logger.handlers`` guard).
        first = ConsoleLogger()
        handler_count_after_first = len(first.logger.handlers)

        # Act
        second = ConsoleLogger()

        # Assert
        self.assertEqual(
            len(second.logger.handlers), handler_count_after_first
        )


class ConsoleLoggerDestructorRemovesHandler(TestCase):
    def test_del_removes_handler_from_underlying_logger(self):
        # Arrange — isolate with a brand-new logger so the shared
        # module-level one doesn't leak handlers between tests.
        console_logger = ConsoleLogger()
        console_logger.logger = MagicMock(spec=logging.Logger)
        handler_sentinel = object()
        console_logger.console_handler = handler_sentinel

        # Act
        console_logger.__del__()

        # Assert
        console_logger.logger.removeHandler.assert_called_once_with(
            handler_sentinel
        )
