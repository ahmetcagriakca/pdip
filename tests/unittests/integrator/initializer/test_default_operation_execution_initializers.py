"""Unit tests for the two no-op default operation initializers.

``DefaultOperationExecutionInitializer`` and
``DefaultOperationIntegrationExecutionInitializer`` are pass-through
implementations that satisfy the abstract contract: ``initialize``
returns its input. These tests exercise both the constructor and the
pass-through behaviour so the default implementations are covered
independently of the factory tests.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.initializer.execution.integration.default_operation_integration_execution_initializer import (  # noqa: E402
    DefaultOperationIntegrationExecutionInitializer,
)
from pdip.integrator.initializer.execution.operation.default_operation_execution_initializer import (  # noqa: E402
    DefaultOperationExecutionInitializer,
)


class DefaultOperationExecutionInitializerContract(TestCase):
    def test_init_constructs_without_state(self):
        subject = DefaultOperationExecutionInitializer()
        self.assertIsInstance(subject, DefaultOperationExecutionInitializer)

    def test_initialize_returns_operation_unchanged(self):
        subject = DefaultOperationExecutionInitializer()
        operation = MagicMock(name="operation")

        result = subject.initialize(operation=operation)

        self.assertIs(result, operation)


class DefaultOperationIntegrationExecutionInitializerContract(TestCase):
    def test_init_constructs_without_state(self):
        subject = DefaultOperationIntegrationExecutionInitializer()
        self.assertIsInstance(
            subject, DefaultOperationIntegrationExecutionInitializer
        )

    def test_initialize_returns_operation_integration_unchanged(self):
        subject = DefaultOperationIntegrationExecutionInitializer()
        operation_integration = MagicMock(name="operation_integration")

        result = subject.initialize(
            operation_integration=operation_integration
        )

        self.assertIs(result, operation_integration)
