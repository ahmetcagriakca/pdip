from injector import inject

from .operation_execution_initializer import OperationExecutionInitializer
from ...operation.domain import OperationBase
from ....dependency import IScoped


class DefaultOperationExecutionInitializer(OperationExecutionInitializer, IScoped):
    @inject
    def __init__(self):
        pass

    def initialize(self, operation: OperationBase) -> OperationBase:
        return operation
