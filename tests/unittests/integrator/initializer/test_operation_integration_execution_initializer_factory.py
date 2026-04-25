"""Unit tests for ``OperationIntegrationExecutionInitializerFactory``.

Same subclass-discovery pattern as its peer factories: default when
alone, custom preferred otherwise, provider is the boundary.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402

from pdip.integrator.initializer.execution.integration.default_operation_integration_execution_initializer import (  # noqa: E402
    DefaultOperationIntegrationExecutionInitializer,
)
from pdip.integrator.initializer.execution.integration.operation_integration_execution_initializer import (  # noqa: E402
    OperationIntegrationExecutionInitializer,
)
from pdip.integrator.initializer.execution.integration.operation_integration_execution_initializer_factory import (  # noqa: E402
    OperationIntegrationExecutionInitializerFactory,
)


class OperationIntegrationExecutionInitializerFactoryChoosesSubclass(TestCase):
    def test_returns_default_when_it_is_the_only_subclass(self):
        provider = MagicMock(name="service_provider")
        sentinel = MagicMock(name="default_initializer")
        provider.get.return_value = sentinel

        factory = OperationIntegrationExecutionInitializerFactory(
            service_provider=provider
        )
        # Pin the subclass list to the default entry so the
        # ``len(subclasses) == 1`` branch runs — other tests in this
        # process may register ad-hoc subclasses that linger.
        with patch.object(
            OperationIntegrationExecutionInitializer,
            "__subclasses__",
            return_value=[DefaultOperationIntegrationExecutionInitializer],
        ):
            result = factory.get()

        self.assertIs(result, sentinel)
        provider.get.assert_called_once_with(
            DefaultOperationIntegrationExecutionInitializer
        )

    def test_prefers_custom_subclass_over_default(self):
        class _Custom(OperationIntegrationExecutionInitializer):
            def initialize(self, operation_integration):
                return operation_integration

        try:
            provider = MagicMock(name="service_provider")
            resolved = MagicMock(name="custom_initializer")
            provider.get.return_value = resolved

            factory = OperationIntegrationExecutionInitializerFactory(
                service_provider=provider
            )
            result = factory.get()

            self.assertIs(result, resolved)
            requested = provider.get.call_args[0][0]
            self.assertIsNot(
                requested, DefaultOperationIntegrationExecutionInitializer
            )
            self.assertTrue(
                issubclass(requested, OperationIntegrationExecutionInitializer)
            )
        finally:
            del _Custom
