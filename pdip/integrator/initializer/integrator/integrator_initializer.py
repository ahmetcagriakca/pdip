from abc import abstractmethod

from pdip.integrator.initializer.base import Initializer
from pdip.integrator.operation.domain import OperationBase
from pdip.integrator.pubsub.base import MessageBroker


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
