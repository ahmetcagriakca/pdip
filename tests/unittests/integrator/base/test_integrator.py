"""Unit tests for ``Integrator`` — the public orchestration entry point.

``Integrator.integrate`` is the single seam the CLI and scheduler call
into. It owns a ``MessageBroker`` per invocation, delegates setup to
``IntegratorInitializerFactory`` and hands execution off to
``OperationExecution``. The multiprocessing broker and SQLAlchemy
collaborators are not exercised here — that is integration-test
territory. All boundaries below are mocked.
"""

# Stub pandas before any pdip.integrator.* import pulls it in via the
# connection adapters' package __init__ chain. See the helper module
# for the rationale.
from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402

from pdip.integrator.operation.domain import OperationBase  # noqa: E402


def _make_integrator(factory=None, operation_execution=None):
    """Construct an ``Integrator`` with the ``MessageBroker`` patched to
    a ``MagicMock`` so no multiprocessing ``Manager`` is started."""
    from pdip.integrator.base import integrator as integrator_module

    logger = MagicMock(name="logger")
    factory = factory if factory is not None else MagicMock(name="factory")
    operation_execution = (
        operation_execution
        if operation_execution is not None
        else MagicMock(name="operation_execution")
    )

    patcher = patch.object(integrator_module, "MessageBroker")
    broker_cls = patcher.start()
    broker = MagicMock(name="broker")
    broker_cls.return_value = broker

    integrator = integrator_module.Integrator(
        logger=logger,
        integrator_initializer_factory=factory,
        operation_execution=operation_execution,
    )
    return integrator, broker, patcher


class IntegratorRejectsInvalidOperation(TestCase):
    def tearDown(self):
        patch.stopall()

    def test_raises_when_operation_is_none(self):
        integrator, _broker, _p = _make_integrator()
        with self.assertRaises(Exception) as ctx:
            integrator.integrate(operation=None)
        self.assertIn("Operation required", str(ctx.exception))

    def test_raises_when_operation_is_not_operation_base(self):
        integrator, _broker, _p = _make_integrator()
        with self.assertRaises(Exception) as ctx:
            integrator.integrate(operation="not an operation")
        self.assertIn("not suitable", str(ctx.exception))


class IntegratorDelegatesToCollaborators(TestCase):
    def tearDown(self):
        patch.stopall()

    def test_integrate_initializes_then_starts_execution(self):
        factory = MagicMock(name="factory")
        initializer = MagicMock(name="initializer")
        initialized_op = MagicMock(name="initialized_op")
        factory.get.return_value = initializer
        initializer.initialize.return_value = initialized_op

        operation_execution = MagicMock(name="operation_execution")
        integrator, broker, _p = _make_integrator(
            factory=factory, operation_execution=operation_execution
        )
        publish_channel = MagicMock(name="publish_channel")
        broker.get_publish_channel.return_value = publish_channel

        operation = OperationBase(Id=1, Name="op", Integrations=[])
        integrator.integrate(operation=operation, execution_id=7, ap_scheduler_job_id=9)

        initializer.initialize.assert_called_once_with(
            operation=operation,
            message_broker=broker,
            execution_id=7,
            ap_scheduler_job_id=9,
        )
        operation_execution.start.assert_called_once_with(
            operation=initialized_op, channel=publish_channel
        )
        # ``join`` always runs via ``finally``.
        broker.join.assert_called_once_with()

    def test_integrate_calls_broker_join_even_when_execution_raises(self):
        factory = MagicMock(name="factory")
        initializer = MagicMock(name="initializer")
        factory.get.return_value = initializer
        initializer.initialize.return_value = MagicMock()

        operation_execution = MagicMock(name="operation_execution")
        operation_execution.start.side_effect = RuntimeError("boom")
        integrator, broker, _p = _make_integrator(
            factory=factory, operation_execution=operation_execution
        )

        operation = OperationBase(Id=2, Name="op2")
        with self.assertRaises(RuntimeError):
            integrator.integrate(operation=operation)

        broker.join.assert_called_once_with()


class IntegratorSubscriptionApiDelegatesToBroker(TestCase):
    def tearDown(self):
        patch.stopall()

    def test_subscribe_and_unsubscribe_forward_to_broker(self):
        integrator, broker, _p = _make_integrator()
        callback = lambda *a, **k: None
        integrator.subscribe("EVENT", callback)
        integrator.unsubscribe("EVENT", callback)
        broker.subscribe.assert_called_once_with("EVENT", callback)
        broker.unsubscribe.assert_called_once_with("EVENT", callback)
