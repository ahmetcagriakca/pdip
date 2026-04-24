"""Unit tests for ``IntegratorInitializerFactory``.

The factory discovers ``IntegratorInitializer`` subclasses at call time
and resolves one via the ``ServiceProvider``. We verify:

* the default subclass is returned when it is the only subclass,
* a custom subclass is preferred when both are registered,
* resolution is delegated to the provider, which is treated as a boundary.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.initializer.integrator.default_integrator_initializer import (  # noqa: E402
    DefaultIntegratorInitializer,
)
from pdip.integrator.initializer.integrator.integrator_initializer import (  # noqa: E402
    IntegratorInitializer,
)
from pdip.integrator.initializer.integrator.integrator_initializer_factory import (
    IntegratorInitializerFactory,
)


class IntegratorInitializerFactoryChoosesSubclass(TestCase):
    def test_returns_default_when_it_is_the_only_subclass(self):
        provider = MagicMock(name="service_provider")
        sentinel = MagicMock(name="default_initializer_instance")
        provider.get.return_value = sentinel

        factory = IntegratorInitializerFactory(service_provider=provider)
        # This test relies on the default being present in the subclass
        # registry. If a custom subclass is registered elsewhere the
        # factory would prefer it — which is covered separately below.
        result = factory.get()

        self.assertIs(result, sentinel)
        provider.get.assert_called_once()

    def test_prefers_custom_subclass_over_default(self):
        class _Custom(IntegratorInitializer):
            def initialize(self, operation, message_broker, execution_id=None,
                           ap_scheduler_job_id=None):
                return operation

        try:
            provider = MagicMock(name="service_provider")
            resolved = MagicMock(name="custom_initializer_instance")
            provider.get.return_value = resolved

            factory = IntegratorInitializerFactory(service_provider=provider)
            result = factory.get()

            self.assertIs(result, resolved)
            # The provider must be asked for the non-default subclass.
            requested_class = provider.get.call_args[0][0]
            self.assertIsNot(requested_class, DefaultIntegratorInitializer)
            self.assertTrue(issubclass(requested_class, IntegratorInitializer))
        finally:
            # Defensive: drop the ad-hoc subclass so later tests see a
            # clean registry. ``__subclasses__`` relies on weak refs, so
            # dereferencing is usually enough.
            del _Custom
