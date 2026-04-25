"""Unit tests for the abstract
``IntegrationSourceToTargetExecuteStrategy`` contract.

The base class has an ``@inject`` no-op ``__init__`` and an
``@abstractmethod`` ``execute`` whose body is ``pass``. Exercise both
through a concrete subclass that calls ``super()``.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.integration.types.sourcetotarget.strategies.base.integration_source_to_target_execute_strategy import (  # noqa: E402
    IntegrationSourceToTargetExecuteStrategy,
)


class _ConcreteStrategy(IntegrationSourceToTargetExecuteStrategy):
    def execute(self, operation_integration, channel):
        return super().execute(operation_integration, channel)


class IntegrationSourceToTargetExecuteStrategyBaseContract(TestCase):
    def test_base_init_runs_without_arguments(self):
        # Arrange + Act
        subject = _ConcreteStrategy()

        # Assert — the concrete subclass is an instance of the ABC.
        self.assertIsInstance(subject, IntegrationSourceToTargetExecuteStrategy)

    def test_super_execute_returns_none(self):
        # Arrange
        subject = _ConcreteStrategy()

        # Act
        result = subject.execute(
            operation_integration=MagicMock(), channel=MagicMock()
        )

        # Assert
        self.assertIsNone(result)
