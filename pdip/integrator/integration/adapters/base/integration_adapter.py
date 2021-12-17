from abc import ABC, abstractmethod

from ...domain.base import IntegrationBase
from ....operation.domain.operation import OperationIntegrationBase
from ....pubsub import EventChannel


class IntegrationAdapter(ABC):
    @abstractmethod
    def execute(
            self,
            operation_integration: OperationIntegrationBase,
            event_channel: EventChannel
    ):
        pass

    @abstractmethod
    def get_start_message(self, integration: IntegrationBase):
        pass

    @abstractmethod
    def get_finish_message(self, integration: IntegrationBase, data_count: int):
        pass

    @abstractmethod
    def get_error_message(self, integration: IntegrationBase):
        pass
