"""Unit tests for the abstract ``Initializer`` contract classes.

Each of the abstract ``*Initializer`` classes declares an
``initialize`` method whose body is a single ``pass`` statement used
only to satisfy the base-class contract for subclasses that invoke
``super().initialize(...)``. These tests call through ``super()`` so
the ``pass`` line executes and the abstract method definition is
covered, without needing to subclass each contract anew in every
adapter suite.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402

from pdip.integrator.initializer.execution.base.execution_initializer import (  # noqa: E402
    ExecutionInitializer,
)
from pdip.integrator.initializer.execution.integration.operation_integration_execution_initializer import (  # noqa: E402
    OperationIntegrationExecutionInitializer,
)
from pdip.integrator.initializer.execution.operation.operation_execution_initializer import (  # noqa: E402
    OperationExecutionInitializer,
)
from pdip.integrator.initializer.integrator.integrator_initializer import (  # noqa: E402
    IntegratorInitializer,
)


class _ConcreteExecutionInitializer(ExecutionInitializer):
    def initialize(self, operation, execution_id=None, ap_scheduler_job_id=None):
        return super().initialize(
            operation,
            execution_id=execution_id,
            ap_scheduler_job_id=ap_scheduler_job_id,
        )


class _ConcreteOperationExecutionInitializer(OperationExecutionInitializer):
    def initialize(self, operation):
        return super().initialize(operation)


class _ConcreteOperationIntegrationExecutionInitializer(
    OperationIntegrationExecutionInitializer
):
    def initialize(self, operation_integration):
        return super().initialize(operation_integration)


class _ConcreteIntegratorInitializer(IntegratorInitializer):
    def initialize(
        self,
        operation,
        message_broker,
        execution_id=None,
        ap_scheduler_job_id=None,
    ):
        return super().initialize(
            operation,
            message_broker,
            execution_id=execution_id,
            ap_scheduler_job_id=ap_scheduler_job_id,
        )


class AbstractExecutionInitializerContract(TestCase):
    def test_super_initialize_returns_none(self):
        subject = _ConcreteExecutionInitializer()
        self.assertIsNone(subject.initialize(operation=object()))


class AbstractOperationExecutionInitializerContract(TestCase):
    def test_super_initialize_returns_none(self):
        subject = _ConcreteOperationExecutionInitializer()
        self.assertIsNone(subject.initialize(operation=object()))


class AbstractOperationIntegrationExecutionInitializerContract(TestCase):
    def test_super_initialize_returns_none(self):
        subject = _ConcreteOperationIntegrationExecutionInitializer()
        self.assertIsNone(subject.initialize(operation_integration=object()))


class AbstractIntegratorInitializerContract(TestCase):
    def test_super_initialize_returns_none(self):
        subject = _ConcreteIntegratorInitializer()
        self.assertIsNone(
            subject.initialize(operation=object(), message_broker=object())
        )
