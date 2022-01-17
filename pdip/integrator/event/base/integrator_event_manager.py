from abc import ABC, abstractmethod

from ...operation.domain import OperationBase, OperationIntegrationBase


class IntegratorEventManager(ABC):
    @abstractmethod
    def log(self, data: any, message: str, exception=None):
        pass

    @abstractmethod
    def initialize(self, data: OperationBase):
        pass

    @abstractmethod
    def start(self, data: OperationBase):
        pass

    @abstractmethod
    def finish(self, data: OperationBase, exception=None):
        pass

    @abstractmethod
    def integration_initialize(self, data: OperationIntegrationBase, message):
        pass

    @abstractmethod
    def integration_start(self, data: OperationIntegrationBase, message):
        pass

    @abstractmethod
    def integration_finish(self, data: OperationIntegrationBase, data_count, message, exception=None):
        pass

    @abstractmethod
    def integration_target_truncate(self, data: OperationIntegrationBase, row_count):
        pass

    @abstractmethod
    def integration_execute_source(self, data: OperationIntegrationBase, row_count):
        pass

    @abstractmethod
    def integration_execute_target(self, data: OperationIntegrationBase, row_count):
        pass
