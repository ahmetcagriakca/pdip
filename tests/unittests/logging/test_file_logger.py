from unittest import TestCase

from pdip.logging.loggers.file import FileLogger


class FileLoggerAcceptsEveryLevel(TestCase):
    """The FileLogger contract is that every level method is callable
    without raising. Assert it explicitly per ADR-0026 A.1 rather than
    relying on the absence of an exception."""

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
