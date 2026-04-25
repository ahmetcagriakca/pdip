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


# ---------------------------------------------------------------------------
# OpenTelemetry instrumentation (ADR-0033 §3) — ``pdip.integrator.job``
# spans wrap the integration body with ``pdip.integration.id`` and
# ``pdip.integration.name`` attributes. Argument-validation errors
# (``Operation required`` / ``not suitable``) intentionally do NOT
# get a span: they are caller mistakes, not job failures.
# ---------------------------------------------------------------------------


class _SpanRecorder:
    """Minimal context-manager span stub. One stub per test; the
    dispatcher tests use the same shape — see ``test_dispatcher.py``."""

    def __init__(self):
        self.attributes = {}
        self.entered = 0
        self.exited = 0

    def __enter__(self):
        self.entered += 1
        return self

    def __exit__(self, exc_type, exc, tb):
        self.exited += 1
        return False

    def set_attribute(self, key, value):
        self.attributes[key] = value


class _TracerRecorder:
    def __init__(self):
        self.span = _SpanRecorder()
        self.span_names = []

    def start_as_current_span(self, name):
        self.span_names.append(name)
        return self.span


class IntegratorEmitsOTelJobSpansPerADR0033(TestCase):
    def tearDown(self):
        patch.stopall()

    def test_integrate_wraps_body_in_pdip_integrator_job_span(self):
        factory = MagicMock(name="factory")
        initializer = MagicMock(name="initializer")
        factory.get.return_value = initializer
        initializer.initialize.return_value = MagicMock()

        operation_execution = MagicMock(name="operation_execution")
        integrator, broker, _p = _make_integrator(
            factory=factory, operation_execution=operation_execution
        )

        tracer = _TracerRecorder()
        from pdip.integrator.base import integrator as integrator_module

        operation = OperationBase(Id=42, Name="weekly-load", Integrations=[])
        with patch.object(
            integrator_module, "get_tracer", return_value=tracer
        ):
            integrator.integrate(operation=operation)

        self.assertEqual(tracer.span_names, ["pdip.integrator.job"])
        self.assertEqual(tracer.span.entered, 1)
        self.assertEqual(tracer.span.exited, 1)
        self.assertEqual(
            tracer.span.attributes.get("pdip.integration.id"), 42
        )
        self.assertEqual(
            tracer.span.attributes.get("pdip.integration.name"),
            "weekly-load",
        )
        broker.join.assert_called_once_with()

    def test_integrate_closes_span_when_execution_raises(self):
        factory = MagicMock(name="factory")
        initializer = MagicMock(name="initializer")
        factory.get.return_value = initializer
        initializer.initialize.return_value = MagicMock()

        operation_execution = MagicMock(name="operation_execution")
        operation_execution.start.side_effect = RuntimeError("boom")
        integrator, broker, _p = _make_integrator(
            factory=factory, operation_execution=operation_execution
        )

        tracer = _TracerRecorder()
        from pdip.integrator.base import integrator as integrator_module

        operation = OperationBase(Id=2, Name="op2")
        with patch.object(
            integrator_module, "get_tracer", return_value=tracer
        ):
            with self.assertRaises(RuntimeError):
                integrator.integrate(operation=operation)

        self.assertEqual(tracer.span.entered, 1)
        self.assertEqual(tracer.span.exited, 1)
        broker.join.assert_called_once_with()

    def test_integrate_falls_back_to_safe_attribute_values_when_fields_none(self):
        # Operation with neither Id nor Name should still produce a
        # span; the recorded attribute values must be SDK-safe (no
        # ``None``s) since OTel's ``set_attribute`` rejects ``None``.
        factory = MagicMock(name="factory")
        initializer = MagicMock(name="initializer")
        factory.get.return_value = initializer
        initializer.initialize.return_value = MagicMock()

        operation_execution = MagicMock(name="operation_execution")
        integrator, _broker, _p = _make_integrator(
            factory=factory, operation_execution=operation_execution
        )

        tracer = _TracerRecorder()
        from pdip.integrator.base import integrator as integrator_module

        operation = OperationBase()  # Id=None, Name=None defaults
        with patch.object(
            integrator_module, "get_tracer", return_value=tracer
        ):
            integrator.integrate(operation=operation)

        self.assertEqual(tracer.span_names, ["pdip.integrator.job"])
        self.assertEqual(tracer.span.attributes.get("pdip.integration.id"), 0)
        self.assertEqual(
            tracer.span.attributes.get("pdip.integration.name"), ""
        )

    def test_argument_validation_errors_do_not_open_a_span(self):
        # ``Operation required`` and ``not suitable`` are caller bugs
        # — they should never appear on a trace as failed jobs.
        integrator, _broker, _p = _make_integrator()

        tracer = _TracerRecorder()
        from pdip.integrator.base import integrator as integrator_module

        with patch.object(
            integrator_module, "get_tracer", return_value=tracer
        ):
            with self.assertRaises(Exception):
                integrator.integrate(operation=None)
            with self.assertRaises(Exception):
                integrator.integrate(operation="not an operation")

        self.assertEqual(tracer.span_names, [])
        self.assertEqual(tracer.span.entered, 0)
