"""Unit tests for ``ExecutionInitializerFactory``.

The factory discovers ``ExecutionInitializer`` subclasses at call
time and delegates resolution to the ``ServiceProvider``. We verify:

* the default subclass is returned when it is the only registered one,
* a custom subclass is preferred when present,
* the provider is treated as a boundary (the factory calls ``get``
  and forwards the resolved instance unchanged).
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.initializer.execution.base.default_execution_initializer import (  # noqa: E402
    DefaultExecutionInitializer,
)
from pdip.integrator.initializer.execution.base.execution_initializer import (  # noqa: E402
    ExecutionInitializer,
)
from pdip.integrator.initializer.execution.base.execution_initializer_factory import (  # noqa: E402
    ExecutionInitializerFactory,
)


class ExecutionInitializerFactoryChoosesSubclass(TestCase):
    def test_returns_default_when_it_is_the_only_subclass(self):
        provider = MagicMock(name="service_provider")
        sentinel = MagicMock(name="default_initializer")
        provider.get.return_value = sentinel

        factory = ExecutionInitializerFactory(service_provider=provider)
        result = factory.get()

        self.assertIs(result, sentinel)
        provider.get.assert_called_once()

    def test_prefers_custom_subclass_over_default(self):
        class _Custom(ExecutionInitializer):
            def initialize(self, operation, execution_id=None, ap_scheduler_job_id=None):
                return operation

        try:
            provider = MagicMock(name="service_provider")
            resolved = MagicMock(name="custom_initializer")
            provider.get.return_value = resolved

            factory = ExecutionInitializerFactory(service_provider=provider)
            result = factory.get()

            self.assertIs(result, resolved)
            requested = provider.get.call_args[0][0]
            self.assertIsNot(requested, DefaultExecutionInitializer)
            self.assertTrue(issubclass(requested, ExecutionInitializer))
        finally:
            del _Custom
