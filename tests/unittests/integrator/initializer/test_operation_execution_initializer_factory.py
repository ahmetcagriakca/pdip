"""Unit tests for ``OperationExecutionInitializerFactory``.

Same subclass-discovery pattern as ``IntegratorInitializerFactory``:
pick the default when alone, prefer a custom subclass otherwise,
delegate resolution to the ``ServiceProvider``.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.initializer.execution.operation.default_operation_execution_initializer import (  # noqa: E402
    DefaultOperationExecutionInitializer,
)
from pdip.integrator.initializer.execution.operation.operation_execution_initializer import (  # noqa: E402
    OperationExecutionInitializer,
)
from pdip.integrator.initializer.execution.operation.operation_execution_initializer_factory import (  # noqa: E402
    OperationExecutionInitializerFactory,
)


class OperationExecutionInitializerFactoryChoosesSubclass(TestCase):
    def test_returns_default_when_it_is_the_only_subclass(self):
        provider = MagicMock(name="service_provider")
        sentinel = MagicMock(name="default_initializer")
        provider.get.return_value = sentinel

        factory = OperationExecutionInitializerFactory(service_provider=provider)
        result = factory.get()

        self.assertIs(result, sentinel)
        provider.get.assert_called_once()

    def test_prefers_custom_subclass_over_default(self):
        class _Custom(OperationExecutionInitializer):
            def initialize(self, operation):
                return operation

        try:
            provider = MagicMock(name="service_provider")
            resolved = MagicMock(name="custom_initializer")
            provider.get.return_value = resolved

            factory = OperationExecutionInitializerFactory(service_provider=provider)
            result = factory.get()

            self.assertIs(result, resolved)
            requested = provider.get.call_args[0][0]
            self.assertIsNot(requested, DefaultOperationExecutionInitializer)
            self.assertTrue(issubclass(requested, OperationExecutionInitializer))
        finally:
            del _Custom
