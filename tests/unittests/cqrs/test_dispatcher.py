"""Unit tests for the CQRS dispatcher.

These tests exercise the dispatch contract without booting the full
``Pdi`` container. A fake service provider is injected directly so that
the handler-discovery convention (see ADR-0003) can be asserted in
isolation from the DI bootstrap.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from pdip.cqrs import (
    Dispatcher,
    ICommand,
    ICommandHandler,
    IQuery,
    IQueryHandler,
)


# ---------------------------------------------------------------------------
# Test fixtures — commands, queries, and their handlers
# ---------------------------------------------------------------------------


class SampleCommand(ICommand):
    def __init__(self, payload: str = "x"):
        super().__init__()
        self.payload = payload


class SampleCommandHandler(ICommandHandler[SampleCommand]):
    calls: list = []

    def handle(self, command: SampleCommand):
        SampleCommandHandler.calls.append(command.payload)


class SampleQuery(IQuery):
    def __init__(self, term: str = "anything"):
        super().__init__()
        self.term = term


class SampleQueryHandler(IQueryHandler[SampleQuery]):
    def handle(self, query: SampleQuery):
        return f"result:{query.term}"


class UnregisteredCommand(ICommand):
    """A command with no matching handler subclass."""

    def __init__(self):
        super().__init__()


# ---------------------------------------------------------------------------
# A service-provider stub that hands back pre-built handler instances
# ---------------------------------------------------------------------------


class FakeServiceProvider:
    def __init__(self, bindings):
        self._bindings = bindings

    def get(self, cls):
        if cls not in self._bindings:
            raise LookupError(f"No binding for {cls!r}")
        return self._bindings[cls]


# ---------------------------------------------------------------------------
# The tests
# ---------------------------------------------------------------------------


class DispatcherFindsHandlerByConvention(TestCase):
    def setUp(self):
        SampleCommandHandler.calls.clear()
        self.provider = FakeServiceProvider(
            {
                SampleCommandHandler: SampleCommandHandler(),
                SampleQueryHandler: SampleQueryHandler(),
            }
        )
        self.dispatcher = Dispatcher(service_provider=self.provider)

    def test_dispatch_routes_command_to_its_handler(self):
        self.dispatcher.dispatch(SampleCommand(payload="hello"))
        self.assertEqual(SampleCommandHandler.calls, ["hello"])

    def test_dispatch_returns_query_handler_result(self):
        result = self.dispatcher.dispatch(SampleQuery(term="world"))
        self.assertEqual(result, "result:world")

    def test_command_dispatch_returns_none(self):
        """Commands do not return a value through dispatch per ADR-0003."""
        self.assertIsNone(self.dispatcher.dispatch(SampleCommand()))


class DispatcherRejectsInvalidInput(TestCase):
    def setUp(self):
        self.provider = FakeServiceProvider({})
        self.dispatcher = Dispatcher(service_provider=self.provider)

    def test_dispatch_raises_when_input_is_neither_command_nor_query(self):
        class NotACQRSRequest:
            pass

        with self.assertRaises(Exception) as ctx:
            self.dispatcher.dispatch(NotACQRSRequest())
        self.assertIn("Command or query not found", str(ctx.exception))

    def test_dispatch_raises_when_no_handler_is_registered(self):
        with self.assertRaises(Exception) as ctx:
            self.dispatcher.dispatch(UnregisteredCommand())
        self.assertIn("Handler not founded", str(ctx.exception))


class DispatcherResolvesHandlerThroughServiceProvider(TestCase):
    def test_handler_instance_is_obtained_from_service_provider(self):
        handler_instance = SampleCommandHandler()
        provider = MagicMock()
        provider.get = MagicMock(return_value=handler_instance)
        dispatcher = Dispatcher(service_provider=provider)

        dispatcher.dispatch(SampleCommand(payload="marker"))

        provider.get.assert_called_once_with(SampleCommandHandler)
        self.assertEqual(SampleCommandHandler.calls[-1], "marker")


# ---------------------------------------------------------------------------
# OpenTelemetry instrumentation (ADR-0033 §3).
#
# Spans are emitted through the lazy helper from ``pdip.observability``;
# we patch the import the dispatcher uses so we can capture the span
# names and attributes without booting the OTel SDK.
# ---------------------------------------------------------------------------


class _SpanRecorder:
    """Minimal context-manager span stub that records every attribute
    the dispatcher sets on it. One stub is shared across all
    ``start_as_current_span`` calls in a test so ``set_attribute``
    history is observable in one place."""

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


class DispatcherEmitsOTelSpansPerADR0033(TestCase):
    def setUp(self):
        SampleCommandHandler.calls.clear()
        self.provider = FakeServiceProvider(
            {
                SampleCommandHandler: SampleCommandHandler(),
                SampleQueryHandler: SampleQueryHandler(),
            }
        )
        self.dispatcher = Dispatcher(service_provider=self.provider)
        self.tracer = _TracerRecorder()

    def test_command_dispatch_emits_pdip_cqrs_command_span(self):
        with patch(
            "pdip.cqrs.dispatcher.get_tracer", return_value=self.tracer
        ):
            self.dispatcher.dispatch(SampleCommand(payload="marker"))

        self.assertEqual(self.tracer.span_names, ["pdip.cqrs.command"])
        self.assertEqual(self.tracer.span.entered, 1)
        self.assertEqual(self.tracer.span.exited, 1)
        self.assertEqual(
            self.tracer.span.attributes.get("pdip.cqrs.handler"),
            "SampleCommandHandler",
        )

    def test_query_dispatch_emits_pdip_cqrs_query_span(self):
        with patch(
            "pdip.cqrs.dispatcher.get_tracer", return_value=self.tracer
        ):
            result = self.dispatcher.dispatch(SampleQuery(term="x"))

        self.assertEqual(result, "result:x")
        self.assertEqual(self.tracer.span_names, ["pdip.cqrs.query"])
        self.assertEqual(
            self.tracer.span.attributes.get("pdip.cqrs.handler"),
            "SampleQueryHandler",
        )

    def test_span_is_closed_when_handler_raises(self):
        # The instrumentation must use ``with`` so the span ends even
        # on exception — otherwise spans leak across requests.
        boom_handler = MagicMock()
        boom_handler.handle.side_effect = RuntimeError("boom")
        provider = MagicMock()
        provider.get = MagicMock(return_value=boom_handler)
        dispatcher = Dispatcher(service_provider=provider)

        with patch(
            "pdip.cqrs.dispatcher.get_tracer", return_value=self.tracer
        ):
            with self.assertRaises(RuntimeError):
                dispatcher.dispatch(SampleCommand(payload="boom"))

        self.assertEqual(self.tracer.span.entered, 1)
        self.assertEqual(self.tracer.span.exited, 1)
