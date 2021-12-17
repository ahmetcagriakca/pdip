from injector import inject

from ..base import IntegrationAdapter
from ...domain.base import IntegrationBase
from ....connection.factories import ConnectionAdapterFactory
from ....models.enums.events import EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE, \
    EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET
from ....operation.domain.operation import OperationIntegrationBase
from ....pubsub import EventChannel
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
            event_channel: EventChannel
    ) -> int:
        target_adapter = self.connection_adapter_factory.get_adapter(
            connection_type=operation_integration.Integration.TargetConnections.ConnectionType)
        if operation_integration.Integration.IsTargetTruncate:
            truncate_affected_row_count = target_adapter.clear_data(integration=operation_integration.Integration)
            event_channel.publish(EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE, operation_integration,
                                  row_count=truncate_affected_row_count)
        affected_row_count = target_adapter.do_target_operation(integration=operation_integration.Integration)
        event_channel.publish(
            EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET,
            operation_integration,
            row_count=affected_row_count
        )
        return affected_row_count

    def get_start_message(self, integration: IntegrationBase):
        return f"Target integration started."

    def get_finish_message(self, integration: IntegrationBase, data_count: int):
        return f"Target integration finished."

    def get_error_message(self, integration: IntegrationBase):
        return f"Target integration getting error."
