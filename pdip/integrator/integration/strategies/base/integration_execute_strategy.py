from abc import ABC, abstractmethod

from injector import inject

from ....operation.domain import OperationIntegrationBase
from ....pubsub.base import ChannelQueue
from .....dependency import IScoped


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
