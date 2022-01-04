from injector import inject

from pdip.dependency import IScoped
from pdip.integrator.connection.domain.authentication.basic import BasicAuthentication
from pdip.integrator.connection.domain.enums import ConnectorTypes, ConnectionTypes
from pdip.integrator.connection.domain.server.base import Server
from pdip.integrator.connection.domain.sql import SqlConnectionConfiguration
from .sql_context import SqlContext
from .sql_policy import SqlPolicy


class SqlProvider(IScoped):
    @inject
    def __init__(self):
        pass

    def __initialize_context(self, config: SqlConnectionConfiguration):
        policy = SqlPolicy(config=config)
        context: SqlContext = SqlContext(policy=policy)
        return context

    def get_context_by_config(self, config: SqlConnectionConfiguration) -> SqlContext:
        return self.__initialize_context(config=config)

    def get_context(self, connector_type: ConnectorTypes, host: str, port: int, user: str, password: str,
                    database: str = None, service_name: str = None, sid: str = None) -> SqlContext:
        """
        Creating Context
        """
        if connector_type == ConnectorTypes.ORACLE:
            config = SqlConnectionConfiguration(ConnectionType=ConnectionTypes.Sql,
                                                ConnectorType=connector_type.ORACLE,
                                                Server=Server(Host=host, Port=port),
                                                BasicAuthentication=BasicAuthentication(User=user, Password=password),
                                                Sid=sid, ServiceName=service_name)
        elif connector_type == ConnectorTypes.MSSQL:
            config = SqlConnectionConfiguration(ConnectionType=ConnectionTypes.Sql,
                                                ConnectorType=ConnectorTypes.MSSQL,
                                                Server=Server(Host=host, Port=port),
                                                BasicAuthentication=BasicAuthentication(User=user, Password=password),
                                                Database=database)
        elif connector_type == ConnectorTypes.POSTGRESQL:
            config = SqlConnectionConfiguration(ConnectionType=ConnectionTypes.Sql,
                                                ConnectorType=ConnectorTypes.POSTGRESQL,
                                                Server=Server(Host=host, Port=port),
                                                BasicAuthentication=BasicAuthentication(User=user, Password=password),
                                                Database=database)
        elif connector_type == ConnectorTypes.MYSQL:
            config = SqlConnectionConfiguration(ConnectionType=ConnectionTypes.Sql,
                                                ConnectorType=ConnectorTypes.MYSQL,
                                                Server=Server(Host=host, Port=port),
                                                BasicAuthentication=BasicAuthentication(User=user, Password=password),
                                                Database=database)
        else:
            raise Exception(f"{connector_type.name} connector type not supported")

        return self.__initialize_context(config=config)
