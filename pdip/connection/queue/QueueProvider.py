from injector import inject

from .QueueContext import QueueContext
from .connectors.KafkaConnector import KafkaConnector
from .connectors.QueueConnector import QueueConnector
from ..models.enums import connection_types, connector_types
from ...dependency.scopes import IScoped
from pdip.logging.loggers.database.sql_logger import SqlLogger


class QueueProvider(IScoped):
    @inject
    def __init__(self,
                 sql_logger: SqlLogger,
                 ):
        self.sql_logger = sql_logger

    def get_context(self, connection, connection_basic_authentication, connection_servers) -> QueueContext:
        """
        Creating Connection
        """
        if connection.ConnectionType.Name == connection_types.Queue.name:
            connector: QueueConnector = None
            if connection.Queue.ConnectorType.Name == connector_types.Kafka.name:
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

        else:
            raise Exception(f"{connection.ConnectionType.Name} connection type not supported")
