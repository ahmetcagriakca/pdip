from typing import List

from injector import inject

from ...integration.base import IntegrationExecution
from ...models.enums.events import EVENT_EXECUTION_INITIALIZED, EVENT_EXECUTION_STARTED, EVENT_EXECUTION_FINISHED
from ...operation.domain import OperationBase, OperationIntegrationBase
from ...pubsub import EventChannel
from ....data.decorators import transactionhandler
from ....dependency import IScoped


class OperationExecution(IScoped):
    @inject
    def __init__(self,
                 integration_execution: IntegrationExecution,
                 ):
        self.integration_execution = integration_execution

    def __start_execution(self, operation_integrations: List[OperationIntegrationBase], event_channel: EventChannel):

        for operation_integration in operation_integrations:
            self.integration_execution.start(operation_integration=operation_integration, event_channel=event_channel)

    @transactionhandler
    def start(self, operation: OperationBase, event_channel: EventChannel):
        try:
            # EVENT_EXECUTION_INITIALIZED = 1
            # EVENT_EXECUTION_STARTED = 2
            # EVENT_EXECUTION_FINISHED = 3
            event_channel.publish(event=EVENT_EXECUTION_INITIALIZED, data=operation)
            event_channel.publish(event=EVENT_EXECUTION_STARTED, data=operation)
            self.__start_execution(operation_integrations=operation.Integrations, event_channel=event_channel)
            event_channel.publish(event=EVENT_EXECUTION_FINISHED, data=operation)
            return "Operation Completed"
        except Exception as ex:
            event_channel.publish(event=EVENT_EXECUTION_FINISHED, data=operation, exception=ex)
            raise
