from typing import List

from injector import inject

from ...integration.base import IntegrationExecution
from ...models.enums.events import EVENT_EXECUTION_INITIALIZED, EVENT_EXECUTION_STARTED, EVENT_EXECUTION_FINISHED
from ...operation.domain import OperationBase, OperationIntegrationBase
from ...pubsub.base import ChannelQueue
from ...pubsub.domain import TaskMessage
from ...pubsub.publisher import Publisher
from ....data.decorators import transactionhandler
from ....dependency import IScoped


class OperationExecution(IScoped):
    @inject
    def __init__(self,
                 integration_execution: IntegrationExecution,
                 ):
        self.integration_execution = integration_execution

    def __start_execution(self, operation_integrations: List[OperationIntegrationBase], channel: ChannelQueue):

        for operation_integration in operation_integrations:
            self.integration_execution.start(operation_integration=operation_integration, channel=channel)

    @transactionhandler
    def start(self, operation: OperationBase, channel: ChannelQueue):
        publisher = Publisher(channel=channel)
        try:
            # EVENT_EXECUTION_INITIALIZED = 1
            # EVENT_EXECUTION_STARTED = 2
            # EVENT_EXECUTION_FINISHED = 3
            publisher.publish(message=TaskMessage(event=EVENT_EXECUTION_INITIALIZED, kwargs={'data': operation}))
            publisher.publish(message=TaskMessage(event=EVENT_EXECUTION_STARTED, kwargs={'data': operation}))
            self.__start_execution(operation_integrations=operation.Integrations, channel=channel)
            publisher.publish(
                message=TaskMessage(event=EVENT_EXECUTION_FINISHED, is_finished=True, kwargs={'data': operation}))
        except Exception as ex:
            publisher.publish(
                message=TaskMessage(event=EVENT_EXECUTION_FINISHED, is_finished=True,
                                    kwargs={'data': operation, 'exception': ex}))
            raise
