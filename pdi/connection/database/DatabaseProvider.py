from injector import inject

from .DatabaseContext import DatabaseContext
from .DatabasePolicy import DatabasePolicy
from ..models.enums import ConnectionTypes, ConnectorTypes
from ...dependency.scopes import IScoped
from ...logging.sql_logger import SqlLogger
from ...configuration.models.database_config import DatabaseConfig


class DatabaseProvider(IScoped):
    @inject
    def __init__(self,
                 sql_logger: SqlLogger,
                 ):
        self.sql_logger = sql_logger

    def get_context(self, connection,connection_basic_authentication,connection_server) -> DatabaseContext:
        """
        Creating Connection
        """
        if connection.ConnectionType.Name == ConnectionTypes.Database.name:
            # connection_basic_authentication = self.operation_cache_service.get_connection_basic_authentication_by_connection_id(
            #     connection_id=connection.Id)
            # connection_server = self.operation_cache_service.get_connection_server_by_connection_id(
            #     connection_id=connection.Id)
            if connection.Database.ConnectorTypeId == ConnectorTypes.ORACLE.value:
                user = connection_basic_authentication.User
                password = connection_basic_authentication.Password
                host = connection_server.Host
                port = connection_server.Port
                service_name = connection.Database.ServiceName
                sid = connection.Database.Sid
                config = DatabaseConfig(type=ConnectorTypes.ORACLE.name, host=host, port=port,
                                        sid=sid, service_name=service_name, username=user, password=password)
            elif connection.Database.ConnectorTypeId == ConnectorTypes.MSSQL.value:
                user = connection_basic_authentication.User
                password = connection_basic_authentication.Password
                host = connection_server.Host
                port = connection_server.Port
                database_name = connection.Database.DatabaseName
                config = DatabaseConfig(type=ConnectorTypes.MSSQL.name, host=host, port=port,
                                        database=database_name, username=user, password=password)
            elif connection.Database.ConnectorTypeId == ConnectorTypes.POSTGRESQL.value:
                user = connection_basic_authentication.User
                password = connection_basic_authentication.Password
                host = connection_server.Host
                port = connection_server.Port
                database_name = connection.Database.DatabaseName
                config = DatabaseConfig(type=ConnectorTypes.POSTGRESQL.name, host=host, port=port,
                                        database=database_name, username=user, password=password)
            elif connection.Database.ConnectorTypeId == ConnectorTypes.MYSQL.value:
                user = connection_basic_authentication.User
                password = connection_basic_authentication.Password
                host = connection_server.Host
                port = connection_server.Port
                database_name = connection.Database.DatabaseName
                config = DatabaseConfig(type=ConnectorTypes.MYSQL.name, host=host, port=port,
                                        database=database_name, username=user, password=password)
            database_policy = DatabasePolicy(database_config=config)
            database_context: DatabaseContext = DatabaseContext(database_policy=database_policy,
                                                                sql_logger=self.sql_logger)
            return database_context
