"""Unit tests for the CQRS dispatcher.

These tests exercise the dispatch contract without booting the full
``Pdi`` container. A fake service provider is injected directly so that
the handler-discovery convention (see ADR-0003) can be asserted in
isolation from the DI bootstrap.
"""

from unittest import TestCase
from unittest.mock import MagicMock

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
