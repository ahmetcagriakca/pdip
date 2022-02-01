from time import time

from injector import inject

from ..types.base import IntegrationAdapter, IntegrationAdapterFactory
from ...domain.enums.events import EVENT_EXECUTION_INTEGRATION_FINISHED, \
    EVENT_EXECUTION_INTEGRATION_STARTED, \
    EVENT_EXECUTION_INTEGRATION_INITIALIZED
from ...initializer.execution.integration import OperationIntegrationExecutionInitializerFactory
from ...operation.domain.operation import OperationIntegrationBase
from ...pubsub.base import ChannelQueue
from ...pubsub.domain import TaskMessage
from ...pubsub.publisher import Publisher
from ....dependency import IScoped


class IntegrationExecution(IScoped):
    @inject
    def __init__(self,
                 integration_adapter_factory: IntegrationAdapterFactory,
                 operation_integration_execution_initializer_factory: OperationIntegrationExecutionInitializerFactory,

                 ):
        self.operation_integration_execution_initializer_factory = operation_integration_execution_initializer_factory
        self.integration_adapter_factory = integration_adapter_factory

    def start(self, operation_integration: OperationIntegrationBase, channel: ChannelQueue):
        start_time = time()
        publisher = Publisher(channel=channel)
        integration_adapter: IntegrationAdapter = self.integration_adapter_factory.get(
            integration=operation_integration.Integration)
        try:
            initializer = self.operation_integration_execution_initializer_factory.get()
            operation_integration = initializer.initialize(operation_integration)
            initialize_message = f'integration initialized.'
            publisher.publish(
                message=TaskMessage(event=EVENT_EXECUTION_INTEGRATION_INITIALIZED,
                                    kwargs={'data': operation_integration,
                                            'message': initialize_message}))

            start_message = integration_adapter.get_start_message(integration=operation_integration.Integration)
            publisher.publish(message=TaskMessage(event=EVENT_EXECUTION_INTEGRATION_STARTED,
                                                  kwargs={'data': operation_integration,
                                                          'message': start_message}))
            data_count = integration_adapter.execute(
                operation_integration=operation_integration,
                channel=channel)

            finish_message = integration_adapter.get_finish_message(integration=operation_integration.Integration,
                                                                    data_count=data_count)

            end_time = time()
            publisher.publish(
                message=TaskMessage(event=EVENT_EXECUTION_INTEGRATION_FINISHED,
                                    kwargs={'data': operation_integration,
                                            'message': f'{finish_message} time:{end_time - start_time}',
                                            'data_count': data_count}))
        except Exception as ex:
            error_message = integration_adapter.get_error_message(integration=operation_integration.Integration)
            publisher.publish(
                message=TaskMessage(event=EVENT_EXECUTION_INTEGRATION_FINISHED,
                                    kwargs={'data': operation_integration,
                                            'message': error_message,
                                            'data_count': 0,
                                            'exception': ex}))
            raise
