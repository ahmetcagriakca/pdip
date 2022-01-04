from injector import inject

from ..base import IntegrationAdapter
from ...domain.base import IntegrationBase
from ....connection.factories import ConnectionAdapterFactory
from ....domain.enums.events import EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE, \
    EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET
from ....operation.domain.operation import OperationIntegrationBase
from ....pubsub.base import ChannelQueue
from ....pubsub.domain import TaskMessage
from ....pubsub.publisher import Publisher
from .....dependency import IScoped


class TargetIntegration(IntegrationAdapter, IScoped):
    @inject
    def __init__(self,
                 connection_adapter_factory: ConnectionAdapterFactory
                 ):
        self.connection_adapter_factory = connection_adapter_factory

    def execute(
            self,
            operation_integration: OperationIntegrationBase,
            channel: ChannelQueue
    ) -> int:
        publisher = Publisher(channel=channel)
        target_adapter = self.connection_adapter_factory.get_adapter(
            connection_type=operation_integration.Integration.TargetConnections.ConnectionType)
        if operation_integration.Integration.IsTargetTruncate:
            truncate_affected_row_count = target_adapter.clear_data(integration=operation_integration.Integration)
            publisher.publish(message=TaskMessage(event=EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE,
                                                  kwargs={"data": operation_integration,
                                                          "row_count": truncate_affected_row_count
                                                          }))
        affected_row_count = target_adapter.do_target_operation(integration=operation_integration.Integration)
        publisher.publish(message=TaskMessage(event=EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET,
                                              kwargs={"data": operation_integration,
                                                      "row_count": affected_row_count
                                                      }))
        return affected_row_count

    def get_start_message(self, integration: IntegrationBase):
        return f"Target integration started."

    def get_finish_message(self, integration: IntegrationBase, data_count: int):
        return f"Target integration finished."

    def get_error_message(self, integration: IntegrationBase):
        return f"Target integration getting error."
