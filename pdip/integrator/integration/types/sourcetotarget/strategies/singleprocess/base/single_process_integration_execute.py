from func_timeout import func_set_timeout
from injector import inject

from ...base import IntegrationSourceToTargetExecuteStrategy
from .......connection.factories import ConnectionSourceAdapterFactory, ConnectionTargetAdapterFactory
from .......domain.enums.events import EVENT_LOG
from .......operation.domain.operation import OperationIntegrationBase
from .......pubsub.base import ChannelQueue
from .......pubsub.domain import TaskMessage
from .......pubsub.publisher import Publisher
from ........dependency import IScoped
from ........observability import get_tracer


def _attr_name(value):
    """Best-effort stringification for the OTel ``pdip.connection.type``
    attribute — accepts both real enums (``ConnectionTypes.Sql``)
    and the bare strings used by some unit-test stubs."""
    return getattr(value, "name", value if isinstance(value, str) else "")


def _resolve_driver(connections):
    """Best-effort ``pdip.connection.driver`` resolution per ADR-0033 §3.

    Looks at the connection-type-specific sub-payload (``Sql`` /
    ``BigData`` / ``WebService``) and reads its
    ``Connection.ConnectorType.name``. Returns ``""`` when the chain
    is incomplete — OTel's ``set_attribute`` rejects ``None`` and the
    span should still emit even when the driver is unresolved (e.g.
    in unit-test stubs that mock the upper layers).
    """
    if connections is None:
        return ""
    for sub_attr in ("Sql", "BigData", "WebService"):
        sub = getattr(connections, sub_attr, None)
        if sub is None:
            continue
        connection = getattr(sub, "Connection", None)
        if connection is None:
            continue
        connector_type = getattr(connection, "ConnectorType", None)
        if connector_type is None:
            continue
        name = getattr(connector_type, "name", None)
        if isinstance(name, str):
            return name
    return ""


class SingleProcessIntegrationExecute(IntegrationSourceToTargetExecuteStrategy, IScoped):
    @inject
    def __init__(self,
                 connection_source_adapter_factory: ConnectionSourceAdapterFactory,
                 connection_target_adapter_factory: ConnectionTargetAdapterFactory
                 ):
        self.connection_source_adapter_factory = connection_source_adapter_factory
        self.connection_target_adapter_factory = connection_target_adapter_factory

    def execute(
            self,
            operation_integration: OperationIntegrationBase,
            channel: ChannelQueue
    ) -> int:
        publisher = Publisher(channel=channel)
        tracer = get_tracer("pdip.integrator")
        try:
            source_connection_type = operation_integration.Integration.SourceConnections.ConnectionType
            target_connection_type = operation_integration.Integration.TargetConnections.ConnectionType
            source_adapter = self.connection_source_adapter_factory.get_adapter(
                connection_type=source_connection_type
            )
            target_adapter = self.connection_target_adapter_factory.get_adapter(
                connection_type=target_connection_type
            )
            integration = operation_integration.Integration
            limit = operation_integration.Limit
            batch_size = limit if limit is not None else 0
            with tracer.start_as_current_span(
                    "pdip.integrator.source.read"
            ) as read_span:
                read_span.set_attribute(
                    "pdip.connection.type", _attr_name(source_connection_type)
                )
                read_span.set_attribute(
                    "pdip.connection.driver",
                    _resolve_driver(integration.SourceConnections),
                )
                read_span.set_attribute("pdip.batch.size", batch_size)
                iterator = source_adapter.get_iterator(
                    integration=integration,
                    limit=limit
                )

            task_id = 0
            start = 0
            data_count = 0
            end = limit
            for results in iterator:
                task_id += 1
                data_length = len(results)
                publisher.publish(
                    message=TaskMessage(
                        event=EVENT_LOG,
                        kwargs={
                            'data': operation_integration,
                            'message': f"0 - data :{task_id}-{start}-{end} readed from db"
                        }
                    )
                )
                with tracer.start_as_current_span(
                        "pdip.integrator.target.write"
                ) as write_span:
                    write_span.set_attribute(
                        "pdip.connection.type",
                        _attr_name(target_connection_type),
                    )
                    write_span.set_attribute(
                        "pdip.connection.driver",
                        _resolve_driver(integration.TargetConnections),
                    )
                    write_span.set_attribute("pdip.batch.size", batch_size)
                    write_span.set_attribute("pdip.rows.written", data_length)
                    self.write_target_data(
                        target_adapter=target_adapter,
                        integration=operation_integration.Integration,
                        source_data=results
                    )
                publisher.publish(
                    message=TaskMessage(
                        event=EVENT_LOG,
                        kwargs={
                            'data': operation_integration,
                            'message': f"0 - data :{task_id}-{start}-{end} process finished task. "
                        }
                    )
                )
                data_count += data_length
                end += limit
                start += limit

            return data_count
        except Exception as ex:
            publisher.publish(
                message=TaskMessage(
                    event=EVENT_LOG,
                    kwargs={
                        'data': operation_integration,
                        'message': f"Integration getting error. ",
                        'exception': ex
                    }
                )
            )
            raise

    @func_set_timeout(1800)
    def write_target_data(
            self,
            target_adapter,
            integration,
            source_data
    ):
        target_adapter.write_data(integration=integration,
                                  source_data=source_data)
