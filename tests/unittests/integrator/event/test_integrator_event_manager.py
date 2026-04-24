"""Unit tests for the abstract base class ``IntegratorEventManager``.

The class declares nine ``@abstractmethod`` hooks with bodies that
are a single ``pass`` each. The coverage gap lives entirely in those
pass-through bodies — they run when a concrete subclass deliberately
delegates to ``super()``.

The ``DefaultIntegratorEventManager`` test module pins down the
default implementation's behaviour; this module pins down:

- Abstract enforcement: the class cannot be instantiated directly
  (ABC contract).
- That each abstract hook has a ``pass`` body, so a subclass that
  calls ``super().method(...)`` gets ``None`` back and no side-effect.
"""

# Stub pandas/func_timeout before any ``pdip.integrator.*`` import
# because this module pulls in operation.domain which touches that
# tree.
from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402

from pdip.integrator.event.base.integrator_event_manager import (  # noqa: E402
    IntegratorEventManager,
)
from pdip.integrator.operation.domain import (  # noqa: E402
    OperationBase,
    OperationIntegrationBase,
)


class _DelegatingManager(IntegratorEventManager):
    """Concrete subclass whose every override calls ``super().method()``
    and records the call. Used to assert the pass-through branches
    in the ABC have been executed."""

    def __init__(self):
        self.calls = []

    def log(self, data, message, exception=None):
        self.calls.append(("log", data, message, exception))
        return super().log(data, message, exception)

    def initialize(self, data):
        self.calls.append(("initialize", data))
        return super().initialize(data)

    def start(self, data):
        self.calls.append(("start", data))
        return super().start(data)

    def finish(self, data, exception=None):
        self.calls.append(("finish", data, exception))
        return super().finish(data, exception)

    def integration_initialize(self, data, message):
        self.calls.append(("integration_initialize", data, message))
        return super().integration_initialize(data, message)

    def integration_start(self, data, message):
        self.calls.append(("integration_start", data, message))
        return super().integration_start(data, message)

    def integration_finish(self, data, data_count, message, exception=None):
        self.calls.append(
            ("integration_finish", data, data_count, message, exception)
        )
        return super().integration_finish(data, data_count, message, exception)

    def integration_target_truncate(self, data, row_count):
        self.calls.append(("integration_target_truncate", data, row_count))
        return super().integration_target_truncate(data, row_count)

    def integration_execute_source(self, data, row_count):
        self.calls.append(("integration_execute_source", data, row_count))
        return super().integration_execute_source(data, row_count)

    def integration_execute_target(self, data, row_count):
        self.calls.append(("integration_execute_target", data, row_count))
        return super().integration_execute_target(data, row_count)


class IntegratorEventManagerIsAbstract(TestCase):
    def test_cannot_instantiate_abstract_base_directly(self):
        # The ABC must reject direct instantiation: otherwise
        # downstream code could accidentally use a non-behaviour
        # event manager.
        with self.assertRaises(TypeError):
            IntegratorEventManager()


class IntegratorEventManagerAbstractMethodsReturnNone(TestCase):
    """When a concrete subclass delegates to ``super()``, every
    abstract body executes its ``pass`` — contract: ``None`` comes
    back and nothing else happens."""

    def setUp(self):
        self.subject = _DelegatingManager()
        self.op = OperationBase(Id=1, Name="op")
        self.oi = OperationIntegrationBase(Id=2, Name="oi", Order=3)

    def test_log_super_returns_none(self):
        result = self.subject.log(
            data=self.op, message="hello", exception=None
        )

        self.assertIsNone(result)
        self.assertIn(("log", self.op, "hello", None), self.subject.calls)

    def test_initialize_super_returns_none(self):
        self.assertIsNone(self.subject.initialize(data=self.op))

    def test_start_super_returns_none(self):
        self.assertIsNone(self.subject.start(data=self.op))

    def test_finish_super_returns_none(self):
        self.assertIsNone(self.subject.finish(data=self.op, exception=None))

    def test_integration_initialize_super_returns_none(self):
        self.assertIsNone(
            self.subject.integration_initialize(data=self.oi, message="m")
        )

    def test_integration_start_super_returns_none(self):
        self.assertIsNone(
            self.subject.integration_start(data=self.oi, message="m")
        )

    def test_integration_finish_super_returns_none(self):
        self.assertIsNone(
            self.subject.integration_finish(
                data=self.oi, data_count=0, message="m", exception=None
            )
        )

    def test_integration_target_truncate_super_returns_none(self):
        self.assertIsNone(
            self.subject.integration_target_truncate(
                data=self.oi, row_count=3
            )
        )

    def test_integration_execute_source_super_returns_none(self):
        self.assertIsNone(
            self.subject.integration_execute_source(
                data=self.oi, row_count=4
            )
        )

    def test_integration_execute_target_super_returns_none(self):
        self.assertIsNone(
            self.subject.integration_execute_target(
                data=self.oi, row_count=5
            )
        )


class IntegratorEventManagerSubclassRecordsEveryCall(TestCase):
    def test_subclass_receives_all_lifecycle_events_in_order(self):
        subject = _DelegatingManager()
        op = OperationBase(Id=1, Name="op")
        oi = OperationIntegrationBase(Id=2, Name="oi", Order=3)

        subject.initialize(data=op)
        subject.start(data=op)
        subject.integration_initialize(data=oi, message="init")
        subject.integration_start(data=oi, message="go")
        subject.integration_execute_source(data=oi, row_count=1)
        subject.integration_execute_target(data=oi, row_count=2)
        subject.integration_target_truncate(data=oi, row_count=3)
        subject.integration_finish(
            data=oi, data_count=2, message="done", exception=None
        )
        subject.finish(data=op, exception=None)

        names = [c[0] for c in subject.calls]
        self.assertEqual(
            names,
            [
                "initialize",
                "start",
                "integration_initialize",
                "integration_start",
                "integration_execute_source",
                "integration_execute_target",
                "integration_target_truncate",
                "integration_finish",
                "finish",
            ],
        )
