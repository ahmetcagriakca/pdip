"""Unit tests for ``pdip.logging.loggers.base.ilogger.ILogger``.

``ILogger`` is the abstract base shared by every logger. Most methods
are placeholders that concrete loggers must override — but they still
need a deterministic no-op contract so partially-implemented test
doubles stay usable. ``prepare_message`` is the single helper with
real formatting logic.
"""

from datetime import datetime
from unittest import TestCase

from pdip.logging.loggers.base.ilogger import ILogger


class ILoggerPrepareMessageFormatsTimestampedEntry(TestCase):
    def test_prepare_message_includes_message_and_process_info(self):
        # Arrange / Act
        formatted = ILogger.prepare_message("payload")

        # Assert
        self.assertIn("payload", formatted)
        self.assertIn("MainProcess", formatted)

    def test_prepare_message_starts_with_iso_like_timestamp(self):
        # Arrange / Act
        formatted = ILogger.prepare_message("x")

        # Assert: the prefix parses back into a datetime with millis.
        stamp = formatted[:23]
        parsed = datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S.%f")
        self.assertIsInstance(parsed, datetime)


class ILoggerDefaultMethodsAreCallablePlaceholders(TestCase):
    """Even though the abstract methods are ``@abstractmethod``-decorated,
    ``ILogger`` is not an ABC — it can still be instantiated, and every
    stub returns ``None``. That's the contract concrete loggers rely on
    when they call ``super()``.
    """

    def setUp(self):
        # Arrange
        self.logger = ILogger()

    def test_log_init_returns_none(self):
        self.assertIsNone(self.logger.log_init())

    def test_log_accepts_level_and_returns_none(self):
        self.assertIsNone(self.logger.log(10, "m"))

    def test_exception_accepts_exception_and_returns_none(self):
        self.assertIsNone(self.logger.exception(RuntimeError("x")))

    def test_critical_returns_none(self):
        self.assertIsNone(self.logger.critical("m"))

    def test_fatal_returns_none(self):
        self.assertIsNone(self.logger.fatal("m"))

    def test_error_returns_none(self):
        self.assertIsNone(self.logger.error("m"))

    def test_warning_returns_none(self):
        self.assertIsNone(self.logger.warning("m"))

    def test_info_returns_none(self):
        self.assertIsNone(self.logger.info("m"))

    def test_debug_returns_none(self):
        self.assertIsNone(self.logger.debug("m"))
