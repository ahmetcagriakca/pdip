from abc import abstractmethod

from ...base import Initializer
from ....operation.domain import OperationBase


class OperationExecutionInitializer(Initializer):
    @abstractmethod
    def initialize(self, operation: OperationBase) -> OperationBase:
        pass
