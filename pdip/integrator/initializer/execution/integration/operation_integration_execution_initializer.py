from abc import abstractmethod

from ...base import Initializer
from ....operation.domain import OperationIntegrationBase


class OperationIntegrationExecutionInitializer(Initializer):
    @abstractmethod
    def initialize(self, operation_integration: OperationIntegrationBase) -> OperationIntegrationBase:
        pass
