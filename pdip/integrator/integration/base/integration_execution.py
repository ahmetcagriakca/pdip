from time import time

from injector import inject

from ..adapters.base import IntegrationAdapter
from ..factories import IntegrationAdapterFactory
from ...models.enums.events import EVENT_EXECUTION_INTEGRATION_FINISHED, EVENT_EXECUTION_INTEGRATION_STARTED, \
    EVENT_EXECUTION_INTEGRATION_INITIALIZED
from ...operation.domain.operation import OperationIntegrationBase
from ...pubsub import EventChannel
from ....dependency import IScoped


class IntegrationExecution(IScoped):
    @inject
    def __init__(self,
                 integration_adapter_factory: IntegrationAdapterFactory
                 ):
        self.integration_adapter_factory = integration_adapter_factory

    def start(self, operation_integration: OperationIntegrationBase, event_channel: EventChannel):
        start_time = time()
        integration_adapter: IntegrationAdapter = self.integration_adapter_factory.get(
            integration=operation_integration.Integration)
        try:
            initialize_message = f'{operation_integration.Integration.Name} integration initialized.'
            event_channel.publish(event=EVENT_EXECUTION_INTEGRATION_INITIALIZED, data=operation_integration,
                                  message=initialize_message)
            start_message = integration_adapter.get_start_message(integration=operation_integration.Integration)
            event_channel.publish(event=EVENT_EXECUTION_INTEGRATION_STARTED, data=operation_integration,
                                  message=start_message)
            data_count = integration_adapter.execute(
                operation_integration=operation_integration,
                event_channel=event_channel)

            finish_message = integration_adapter.get_finish_message(integration=operation_integration.Integration,
                                                                    data_count=data_count)

            end_time = time()
            event_channel.publish(event=EVENT_EXECUTION_INTEGRATION_FINISHED, data=operation_integration, data_count=data_count,
                                  message=f'{finish_message} time:{end_time - start_time}')
        except Exception as ex:
            error_message = integration_adapter.get_error_message(integration=operation_integration.Integration)
            event_channel.publish(event=EVENT_EXECUTION_INTEGRATION_FINISHED, data=operation_integration,
                                  message=error_message, exception=ex)
            raise
