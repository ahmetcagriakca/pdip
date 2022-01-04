from injector import inject

from ...base import Initializer
from ...operation.domain import OperationIntegrationBase


class OperationIntegrationInitializer(Initializer):
    @inject
    def initialize(self, operation_integration: OperationIntegrationBase) -> int:
        pass
