"""Unit tests for ``pdip.processing.factories.process_manager_factory``.

The factory is injected with a logger and exposes ``get()``, which
builds a ``ProcessManager`` bound to that same logger. The behaviour
contract is narrow: constructor stores the collaborator and
``get()`` wires it into a fresh ``ProcessManager``.
"""

from unittest import TestCase
from unittest.mock import MagicMock

from pdip.processing import ProcessManager
from pdip.processing.factories.process_manager_factory import (
    ProcessManagerFactory,
)


class ProcessManagerFactoryStoresLogger(TestCase):
    def test_init_stores_logger_collaborator(self):
        logger = MagicMock(name="logger")

        factory = ProcessManagerFactory(logger=logger)

        self.assertIs(factory.logger, logger)


class ProcessManagerFactoryGetReturnsWiredManager(TestCase):
    def test_get_returns_process_manager_instance(self):
        factory = ProcessManagerFactory(logger=MagicMock(name="logger"))

        manager = factory.get()

        self.assertIsInstance(manager, ProcessManager)

    def test_get_injects_the_factorys_logger_into_process_manager(self):
        logger = MagicMock(name="logger")
        factory = ProcessManagerFactory(logger=logger)

        manager = factory.get()

        self.assertIs(manager.logger, logger)

    def test_get_returns_a_fresh_manager_each_call(self):
        factory = ProcessManagerFactory(logger=MagicMock(name="logger"))

        first = factory.get()
        second = factory.get()

        self.assertIsNot(first, second)
