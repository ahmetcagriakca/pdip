"""Unit tests for the CQRS base-class stubs.

These module-level contract classes (``CommandQueryBase``,
``CommandQueryHandlerBase``, ``ICommandHandler``, ``IQueryHandler``)
expose ``__init__`` / ``handle`` no-ops that exist to anchor a shared
signature for concrete implementations. Each stub body is a single
``pass`` — exercise it so the contract lines are covered and a
regression to the signatures lands here.
"""

from unittest import TestCase

from pdip.cqrs.command_query_base import CommandQueryBase
from pdip.cqrs.command_query_handler_base import CommandQueryHandlerBase
from pdip.cqrs.icommand_handler import ICommandHandler
from pdip.cqrs.iquery_handler import IQueryHandler


class CommandQueryBaseStubConstructs(TestCase):
    def test_instantiation_does_not_raise(self):
        # Arrange + Act
        instance = CommandQueryBase()

        # Assert
        self.assertIsInstance(instance, CommandQueryBase)


class CommandQueryHandlerBaseStubs(TestCase):
    def test_init_stub_returns_instance(self):
        instance = CommandQueryHandlerBase()

        self.assertIsInstance(instance, CommandQueryHandlerBase)

    def test_handle_stub_returns_none(self):
        instance = CommandQueryHandlerBase()

        self.assertIsNone(instance.handle(query=object()))


class ICommandHandlerStubs(TestCase):
    def test_init_stub_returns_instance(self):
        instance = ICommandHandler()

        self.assertIsInstance(instance, ICommandHandler)

    def test_handle_stub_returns_none(self):
        instance = ICommandHandler()

        self.assertIsNone(instance.handle(query=object()))


class IQueryHandlerStubs(TestCase):
    def test_init_stub_returns_instance(self):
        instance = IQueryHandler()

        self.assertIsInstance(instance, IQueryHandler)

    def test_handle_stub_returns_none(self):
        instance = IQueryHandler()

        self.assertIsNone(instance.handle(query=object()))
