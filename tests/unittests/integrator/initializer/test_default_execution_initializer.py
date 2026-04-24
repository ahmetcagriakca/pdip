"""Unit tests for ``DefaultExecutionInitializer``.

The default implementation wraps an ``OperationBase`` in an
``ExecutionOperationBase`` and each of its integrations in an
``ExecutionOperationIntegrationBase``, propagating the scheduler ids.
These tests drive the initializer directly with stub
``OperationBase``/``OperationIntegrationBase`` instances and assert
the resulting execution objects.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402

from pdip.integrator.initializer.execution.base.default_execution_initializer import (  # noqa: E402
    DefaultExecutionInitializer,
)
from pdip.integrator.operation.domain import (  # noqa: E402
    OperationBase,
    OperationIntegrationBase,
)


class DefaultExecutionInitializerWrapsOperation(TestCase):
    def test_init_stores_no_state(self):
        # Constructor is a pure ``pass`` but must still be exercised
        # for coverage. A plain instantiation is all that's needed.
        subject = DefaultExecutionInitializer()
        self.assertIsInstance(subject, DefaultExecutionInitializer)

    def test_initialize_returns_same_operation_instance(self):
        subject = DefaultExecutionInitializer()
        operation = OperationBase(Id=1, Name="op", Integrations=[])

        returned = subject.initialize(
            operation=operation, execution_id=42, ap_scheduler_job_id=7
        )

        self.assertIs(returned, operation)

    def test_initialize_attaches_execution_operation_to_operation(self):
        subject = DefaultExecutionInitializer()
        operation = OperationBase(Id=5, Name="demo", Integrations=[])

        subject.initialize(
            operation=operation, execution_id=101, ap_scheduler_job_id=202
        )

        self.assertIsNotNone(operation.Execution)
        self.assertEqual(operation.Execution.Id, 101)
        self.assertEqual(operation.Execution.ApSchedulerJobId, 202)
        self.assertEqual(operation.Execution.OperationId, 5)
        self.assertEqual(operation.Execution.Name, "demo")
        self.assertEqual(operation.Execution.Events, [])

    def test_initialize_wraps_each_integration_with_execution_wrapper(self):
        subject = DefaultExecutionInitializer()
        integration_a = OperationIntegrationBase(Id=11, Name="a", Order=1)
        integration_b = OperationIntegrationBase(Id=12, Name="b", Order=2)
        operation = OperationBase(
            Id=9, Name="op", Integrations=[integration_a, integration_b]
        )

        subject.initialize(
            operation=operation, execution_id=501, ap_scheduler_job_id=777
        )

        self.assertIsNotNone(integration_a.Execution)
        self.assertEqual(integration_a.Execution.OperationId, 9)
        self.assertEqual(integration_a.Execution.OperationIntegrationId, 11)
        self.assertEqual(integration_a.Execution.OperationExecutionId, 501)
        self.assertEqual(integration_a.Execution.ApSchedulerJobId, 777)
        self.assertEqual(integration_a.Execution.Name, "a")
        self.assertEqual(integration_a.Execution.Events, [])

        self.assertIsNotNone(integration_b.Execution)
        self.assertEqual(integration_b.Execution.OperationIntegrationId, 12)
        self.assertEqual(integration_b.Execution.Name, "b")

    def test_initialize_handles_empty_integrations_list(self):
        subject = DefaultExecutionInitializer()
        operation = OperationBase(Id=1, Name="empty", Integrations=[])

        subject.initialize(operation=operation)

        # Execution is still attached; loop body never runs.
        self.assertIsNotNone(operation.Execution)
        self.assertIsNone(operation.Execution.Id)
        self.assertIsNone(operation.Execution.ApSchedulerJobId)

    def test_initialize_defaults_ids_to_none_when_not_provided(self):
        subject = DefaultExecutionInitializer()
        integration = OperationIntegrationBase(Id=3, Name="x")
        operation = OperationBase(Id=2, Name="y", Integrations=[integration])

        subject.initialize(operation=operation)

        self.assertIsNone(operation.Execution.Id)
        self.assertIsNone(operation.Execution.ApSchedulerJobId)
        self.assertIsNone(integration.Execution.OperationExecutionId)
        self.assertIsNone(integration.Execution.ApSchedulerJobId)
