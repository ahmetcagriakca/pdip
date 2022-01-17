from injector import inject

from .execution_initializer import ExecutionInitializer
from ...execution.domain import ExecutionOperationBase, ExecutionOperationIntegrationBase
from ...operation.domain import OperationBase
from ....dependency import IScoped


class DefaultExecutionInitializer(ExecutionInitializer, IScoped):
    @inject
    def __init__(self):
        pass

    def initialize(
            self,
            operation: OperationBase,
            execution_id: int = None,
            ap_scheduler_job_id: int = None
    ) -> OperationBase:
        execution_operation = ExecutionOperationBase(
            Id=execution_id,
            ApSchedulerJobId=ap_scheduler_job_id,
            OperationId=operation.Id,
            Name=operation.Name,
            Events=[]
        )
        operation.Execution = execution_operation

        for operation_integration in operation.Integrations:
            execution_operation_integration = ExecutionOperationIntegrationBase(
                Id=None,
                OperationId=operation.Id,
                OperationExecutionId=execution_id,
                ApSchedulerJobId=ap_scheduler_job_id,
                OperationIntegrationId=operation_integration.Id,
                Name=operation_integration.Name,
                Events=[]
            )
            operation_integration.Execution = execution_operation_integration
        return operation
