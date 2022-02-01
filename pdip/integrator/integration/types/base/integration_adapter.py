from abc import ABC, abstractmethod

from pdip.integrator.integration.domain.base import IntegrationBase
from pdip.integrator.operation.domain.operation import OperationIntegrationBase
from pdip.integrator.pubsub.base import ChannelQueue


class IntegrationAdapter(ABC):
    @abstractmethod
    def execute(
            self,
            operation_integration: OperationIntegrationBase,
            channel: ChannelQueue
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
