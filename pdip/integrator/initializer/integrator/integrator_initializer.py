from abc import abstractmethod

from ..base import Initializer
from ...operation.domain import OperationBase
from ...pubsub.base import MessageBroker


class IntegratorInitializer(Initializer):
    @abstractmethod
    def initialize(
            self,
            operation: OperationBase,
            message_broker: MessageBroker,
            execution_id: int = None,
            ap_scheduler_job_id: int = None
    ) -> OperationBase:
        pass
