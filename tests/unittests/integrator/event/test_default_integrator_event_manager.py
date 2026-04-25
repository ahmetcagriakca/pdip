"""Unit tests for ``DefaultIntegratorEventManager``.

The default event manager forwards lifecycle callbacks to a
``ConsoleLogger`` as human-readable ``info`` / ``exception`` lines.
Every test pins down both which logger method is called and the
exact formatted message, because the message format is the contract
with downstream log consumers.

``integration_execute_target`` sleeps 2s at the end of its body; we
patch ``time.sleep`` on the subject's module to keep the test fast
and to respect ADR-0026 D.1. See the note at the bottom of the PR
description.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from pdip.integrator.event.base import default_integrator_event_manager
from pdip.integrator.event.base.default_integrator_event_manager import (
    DefaultIntegratorEventManager,
)
from pdip.integrator.operation.domain import (
    OperationBase,
    OperationIntegrationBase,
)


def _build_subject():
    """Return ``(subject, logger)`` with a mock logger wired in."""
    logger = MagicMock(name="logger")
    subject = DefaultIntegratorEventManager(logger=logger)
    return subject, logger


class DefaultIntegratorEventManagerLog(TestCase):
    def test_log_operation_info_uses_name_only_when_no_exception(self):
        subject, logger = _build_subject()
        data = OperationBase(Id=1, Name="op-1")

        subject.log(data=data, message="hello")

        logger.info.assert_called_once_with("op-1 - hello")
        logger.exception.assert_not_called()

    def test_log_operation_exception_forwards_exception_and_name(self):
        subject, logger = _build_subject()
        data = OperationBase(Id=1, Name="op-1")
        boom = RuntimeError("boom")

        subject.log(data=data, message="failed", exception=boom)

        logger.exception.assert_called_once_with(boom, "op-1 - failed")
        logger.info.assert_not_called()

    def test_log_integration_info_uses_order_and_name(self):
        subject, logger = _build_subject()
        data = OperationIntegrationBase(Id=1, Name="oi-1", Order=3)

        subject.log(data=data, message="hello")

        logger.info.assert_called_once_with("3 - oi-1 - hello")

    def test_log_integration_exception_uses_order_and_name(self):
        subject, logger = _build_subject()
        data = OperationIntegrationBase(Id=1, Name="oi-1", Order=3)
        boom = ValueError("bad")

        subject.log(data=data, message="died", exception=boom)

        logger.exception.assert_called_once_with(boom, "3 - oi-1 - died")


class DefaultIntegratorEventManagerLifecycle(TestCase):
    def test_initialize_logs_name_with_initialized_suffix(self):
        subject, logger = _build_subject()
        data = OperationBase(Id=1, Name="op-1")

        subject.initialize(data=data)

        logger.info.assert_called_once_with("op-1 initialized.")

    def test_start_logs_name_with_started_suffix(self):
        subject, logger = _build_subject()
        data = OperationBase(Id=1, Name="op-1")

        subject.start(data=data)

        logger.info.assert_called_once_with("op-1 started.")

    def test_finish_without_exception_logs_name_finished(self):
        subject, logger = _build_subject()
        data = OperationBase(Id=1, Name="op-1")

        subject.finish(data=data)

        logger.info.assert_called_once_with("op-1 finished.")
        logger.exception.assert_not_called()

    def test_finish_with_exception_uses_logger_exception(self):
        subject, logger = _build_subject()
        data = OperationBase(Id=1, Name="op-1")
        boom = RuntimeError("boom")

        subject.finish(data=data, exception=boom)

        logger.exception.assert_called_once_with(boom, "op-1 finished with error.")
        logger.info.assert_not_called()


class DefaultIntegratorEventManagerIntegrationLifecycle(TestCase):
    def test_integration_initialize_formats_order_name_and_message(self):
        subject, logger = _build_subject()
        data = OperationIntegrationBase(Id=1, Name="oi", Order=2)

        subject.integration_initialize(data=data, message="ready")

        logger.info.assert_called_once_with("2 - oi - ready")

    def test_integration_start_formats_order_name_and_message(self):
        subject, logger = _build_subject()
        data = OperationIntegrationBase(Id=1, Name="oi", Order=4)

        subject.integration_start(data=data, message="go")

        logger.info.assert_called_once_with("4 - oi - go")

    def test_integration_finish_without_exception_uses_info(self):
        subject, logger = _build_subject()
        data = OperationIntegrationBase(Id=1, Name="oi", Order=7)

        subject.integration_finish(data=data, data_count=5, message="done")

        logger.info.assert_called_once_with("7 - oi - done")
        logger.exception.assert_not_called()

    def test_integration_finish_with_exception_uses_exception(self):
        subject, logger = _build_subject()
        data = OperationIntegrationBase(Id=1, Name="oi", Order=7)
        boom = RuntimeError("boom")

        subject.integration_finish(
            data=data, data_count=0, message="broke", exception=boom
        )

        logger.exception.assert_called_once_with(boom, "7 - oi - broke")
        logger.info.assert_not_called()


class DefaultIntegratorEventManagerCounters(TestCase):
    def test_integration_target_truncate_logs_row_count_in_message(self):
        subject, logger = _build_subject()
        data = OperationIntegrationBase(Id=1, Name="oi", Order=1)

        subject.integration_target_truncate(data=data, row_count=10)

        logger.info.assert_called_once_with(
            "1 - oi - Target truncate finished. (Affected Row Count:10)"
        )

    def test_integration_execute_source_logs_row_count_in_message(self):
        subject, logger = _build_subject()
        data = OperationIntegrationBase(Id=1, Name="oi", Order=6)

        subject.integration_execute_source(data=data, row_count=42)

        logger.info.assert_called_once_with(
            "6 - oi - Source integration completed. (Source Data Count:42)"
        )

    def test_integration_execute_target_logs_row_count_in_message(self):
        subject, logger = _build_subject()
        data = OperationIntegrationBase(Id=1, Name="oi", Order=8)
        slept = MagicMock(name="sleep_fn")

        # The production method sleeps 2 seconds after emitting the log
        # but accepts an injectable sleep_fn so tests keep sub-second
        # (ADR-0026 D.1). Pass a spy so we assert the delay arg without
        # blocking the test runner.
        subject.integration_execute_target(data=data, row_count=11, sleep_fn=slept)

        logger.info.assert_called_once_with(
            "8 - oi - Target integration completed. (Affected Row Count:11)"
        )
        slept.assert_called_once_with(2)

    def test_integration_execute_target_defaults_to_time_sleep_when_no_fn_given(self):
        subject, logger = _build_subject()
        data = OperationIntegrationBase(Id=1, Name="oi", Order=8)

        # When no sleep_fn is passed the subject falls back to
        # ``time.sleep`` on its module; patch it so the test stays fast.
        with patch.object(default_integrator_event_manager.time, "sleep") as slept:
            subject.integration_execute_target(data=data, row_count=3)

        logger.info.assert_called_once_with(
            "8 - oi - Target integration completed. (Affected Row Count:3)"
        )
        slept.assert_called_once_with(2)
