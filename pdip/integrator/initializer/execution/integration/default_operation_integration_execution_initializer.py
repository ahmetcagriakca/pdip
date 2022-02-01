from injector import inject

from .operation_integration_execution_initializer import OperationIntegrationExecutionInitializer
from ...operation.domain import OperationIntegrationBase
from ....dependency import IScoped


class DefaultOperationIntegrationExecutionInitializer(OperationIntegrationExecutionInitializer, IScoped):
    @inject
    def __init__(self):
        pass

    def initialize(self, operation_integration: OperationIntegrationBase) -> OperationIntegrationBase:
        return operation_integration
