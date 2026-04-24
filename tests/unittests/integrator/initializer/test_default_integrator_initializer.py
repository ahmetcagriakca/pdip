"""Unit tests for ``DefaultIntegratorInitializer``.

The default initializer wires the message broker, subscribes the
event manager to every lifecycle event, starts the broker, and
delegates to the injected ``ExecutionInitializerFactory``. Each
interaction is a contract with the broker, so we verify them by
capturing subscriptions via a mock broker rather than spinning up a
real one.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.domain.enums.events import (  # noqa: E402
    EVENT_EXECUTION_FINISHED,
    EVENT_EXECUTION_INITIALIZED,
    EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE,
    EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET,
    EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE,
    EVENT_EXECUTION_INTEGRATION_FINISHED,
    EVENT_EXECUTION_INTEGRATION_INITIALIZED,
    EVENT_EXECUTION_INTEGRATION_STARTED,
    EVENT_EXECUTION_STARTED,
    EVENT_LOG,
)
from pdip.integrator.initializer.integrator.default_integrator_initializer import (  # noqa: E402
    DefaultIntegratorInitializer,
)


def _build_subject():
    event_manager = MagicMock(name="event_manager")
    event_manager_factory = MagicMock(name="event_manager_factory")
    event_manager_factory.get.return_value = event_manager

    execution_initializer = MagicMock(name="execution_initializer")
    execution_initializer.initialize.side_effect = lambda operation, execution_id=None, ap_scheduler_job_id=None: operation  # noqa: E501
    execution_initializer_factory = MagicMock(name="execution_initializer_factory")
    execution_initializer_factory.get.return_value = execution_initializer

    subject = DefaultIntegratorInitializer(
        integrator_event_manager_factory=event_manager_factory,
        execution_initializer_factory=execution_initializer_factory,
    )
    return subject, event_manager, execution_initializer


class DefaultIntegratorInitializerInitialize(TestCase):
    def test_broker_is_initialized_then_started(self):
        subject, _event_manager, _init = _build_subject()
        broker = MagicMock(name="broker")
        call_order = []
        broker.initialize.side_effect = lambda: call_order.append("initialize")
        broker.start.side_effect = lambda: call_order.append("start")
        operation = MagicMock(name="operation")

        subject.initialize(operation=operation, message_broker=broker)

        self.assertEqual(call_order, ["initialize", "start"])

    def test_returns_the_operation_from_execution_initializer(self):
        subject, _event_manager, execution_initializer = _build_subject()
        broker = MagicMock(name="broker")
        returned = MagicMock(name="returned_operation")
        execution_initializer.initialize.side_effect = None
        execution_initializer.initialize.return_value = returned
        operation = MagicMock(name="operation")

        result = subject.initialize(operation=operation, message_broker=broker)

        self.assertIs(result, returned)

    def test_passes_execution_and_scheduler_ids_to_inner_initializer(self):
        subject, _event_manager, execution_initializer = _build_subject()
        broker = MagicMock(name="broker")
        operation = MagicMock(name="operation")

        subject.initialize(
            operation=operation,
            message_broker=broker,
            execution_id=77,
            ap_scheduler_job_id=99,
        )

        execution_initializer.initialize.assert_called_once_with(
            operation=operation,
            execution_id=77,
            ap_scheduler_job_id=99,
        )


class DefaultIntegratorInitializerRegistersAllEventListeners(TestCase):
    def test_every_lifecycle_event_is_subscribed_exactly_once(self):
        subject, event_manager, _init = _build_subject()
        broker = MagicMock(name="broker")

        subject.register_default_event_listeners(broker)

        expected = {
            EVENT_LOG: event_manager.log,
            EVENT_EXECUTION_INITIALIZED: event_manager.initialize,
            EVENT_EXECUTION_STARTED: event_manager.start,
            EVENT_EXECUTION_FINISHED: event_manager.finish,
            EVENT_EXECUTION_INTEGRATION_INITIALIZED: event_manager.integration_initialize,  # noqa: E501
            EVENT_EXECUTION_INTEGRATION_STARTED: event_manager.integration_start,
            EVENT_EXECUTION_INTEGRATION_FINISHED: event_manager.integration_finish,
            EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE: event_manager.integration_target_truncate,  # noqa: E501
            EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE: event_manager.integration_execute_source,  # noqa: E501
            EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET: event_manager.integration_execute_target,  # noqa: E501
        }
        calls = broker.subscribe.call_args_list
        registered = {call.args[0]: call.args[1] for call in calls}
        self.assertEqual(registered, expected)
