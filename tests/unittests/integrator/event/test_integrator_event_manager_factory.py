"""Unit tests for ``IntegratorEventManagerFactory``.

Same subclass-discovery pattern as the initializer factories:

* return the default when it is the only registered subclass,
* prefer a custom subclass when both are registered,
* delegate resolution to the ``ServiceProvider``.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402

from pdip.integrator.event.base.default_integrator_event_manager import (  # noqa: E402
    DefaultIntegratorEventManager,
)
from pdip.integrator.event.base.integrator_event_manager import (  # noqa: E402
    IntegratorEventManager,
)
from pdip.integrator.event.base.integrator_event_manager_factory import (  # noqa: E402
    IntegratorEventManagerFactory,
)


class IntegratorEventManagerFactoryChoosesSubclass(TestCase):
    def test_returns_default_when_it_is_the_only_subclass(self):
        provider = MagicMock(name="service_provider")
        sentinel = MagicMock(name="default_event_manager")
        provider.get.return_value = sentinel

        factory = IntegratorEventManagerFactory(service_provider=provider)
        # Pin the subclass list to the default entry so the
        # ``len(subclasses) == 1`` branch runs — other tests in this
        # process may register ad-hoc subclasses that linger.
        with patch.object(
            IntegratorEventManager,
            "__subclasses__",
            return_value=[DefaultIntegratorEventManager],
        ):
            result = factory.get()

        self.assertIs(result, sentinel)
        provider.get.assert_called_once_with(DefaultIntegratorEventManager)

    def test_prefers_custom_subclass_over_default(self):
        class _Custom(IntegratorEventManager):
            def log(self, data, message, exception=None):
                return None

            def initialize(self, data):
                return None

            def start(self, data):
                return None

            def finish(self, data, exception=None):
                return None

            def integration_initialize(self, data, message):
                return None

            def integration_start(self, data, message):
                return None

            def integration_finish(self, data, data_count, message, exception=None):
                return None

            def integration_target_truncate(self, data, row_count):
                return None

            def integration_execute_source(self, data, row_count):
                return None

            def integration_execute_target(self, data, row_count):
                return None

        try:
            provider = MagicMock(name="service_provider")
            resolved = MagicMock(name="custom_event_manager")
            provider.get.return_value = resolved

            factory = IntegratorEventManagerFactory(service_provider=provider)
            result = factory.get()

            self.assertIs(result, resolved)
            requested = provider.get.call_args[0][0]
            self.assertIsNot(requested, DefaultIntegratorEventManager)
            self.assertTrue(issubclass(requested, IntegratorEventManager))
        finally:
            del _Custom
