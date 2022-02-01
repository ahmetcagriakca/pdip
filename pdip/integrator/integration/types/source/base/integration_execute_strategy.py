from abc import ABC, abstractmethod

from injector import inject
from pdip.dependency import IScoped
from pdip.integrator.operation.domain import OperationIntegrationBase
from pdip.integrator.pubsub.base import ChannelQueue


class IntegrationExecuteStrategy(ABC, IScoped):
    @inject
    def __init__(self):
        pass

    @abstractmethod
    def execute(
            self,
            operation_integration: OperationIntegrationBase,
            channel: ChannelQueue
    ) -> int:
        pass
