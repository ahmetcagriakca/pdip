from injector import inject

from pdip.integrator.base import Initializer
from pdip.integrator.operation.domain import OperationBase


class OperationInitializer(Initializer):
    @inject
    def initialize(self, operation: OperationBase) -> int:
        pass