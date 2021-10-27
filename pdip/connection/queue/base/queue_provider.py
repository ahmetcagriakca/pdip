from injector import inject

from .queue_connector import QueueConnector
from .queue_context import QueueContext
from ..connectors import KafkaConnector
from ...models.enums import ConnectorTypes
from ....dependency import IScoped


class QueueProvider(IScoped):
    @inject
    def __init__(self,
                 ):
        pass

    def get_context(self, connection, connection_basic_authentication, connection_servers) -> QueueContext:
        """
        Creating Connection
        """
        connector: QueueConnector = None
        if connection.Queue.ConnectorType.Name == ConnectorTypes.Kafka.name:
            servers = []
            for connection_server in connection_servers:
                server = f"{connection_server.Host}:{connection_server.Port}"
                servers.append(server)
            auth = None
            if ((connection.Queue.Protocol is not None and connection.Queue.Protocol != '') and (
                    connection.Queue.Mechanism is not None and connection.Queue.Mechanism != '') and (
                    connection_basic_authentication.User is not None and connection_basic_authentication.User != '') and (
                    connection_basic_authentication.Password is not None and connection_basic_authentication.Password != '')):
                auth = {
                    'security_protocol': connection.Queue.Protocol,
                    'sasl_mechanism': connection.Queue.Mechanism,
                    'sasl_plain_username': connection_basic_authentication.User,
                    'sasl_plain_password': connection_basic_authentication.Password
                }
            connector = KafkaConnector(servers=servers, auth=auth)
        if connector is not None:
            queue_context: QueueContext = QueueContext(connector=connector)
            return queue_context
        else:
            raise Exception(f"{connection.Queue.ConnectorType.Name} connector type not supported")
