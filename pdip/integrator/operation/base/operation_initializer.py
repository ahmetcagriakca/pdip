from injector import inject

from ..domain import OperationBase
from ...base import Initializer


class OperationInitializer(Initializer):
    @inject
    def initialize(self, operation: OperationBase) -> int:
        pass
