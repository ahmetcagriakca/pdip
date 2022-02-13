from injector import inject

from .sql_context import SqlContext
from .sql_policy import SqlPolicy
from ....domain.authentication.basic import ConnectionBasicAuthentication
from ....domain.enums import ConnectorTypes, ConnectionTypes
from ....domain.server.base import ConnectionServer
from ....domain.types.sql.configuration.base import SqlConnectionConfiguration
from ......dependency import IScoped


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
                                                Server=ConnectionServer(Host=host, Port=port),
                                                BasicAuthentication=ConnectionBasicAuthentication(User=user, Password=password),
                                                Sid=sid, ServiceName=service_name)
        elif connector_type == ConnectorTypes.MSSQL:
            config = SqlConnectionConfiguration(ConnectionType=ConnectionTypes.Sql,
                                                ConnectorType=ConnectorTypes.MSSQL,
                                                Server=ConnectionServer(Host=host, Port=port),
                                                BasicAuthentication=ConnectionBasicAuthentication(User=user, Password=password),
                                                Database=database)
        elif connector_type == ConnectorTypes.POSTGRESQL:
            config = SqlConnectionConfiguration(ConnectionType=ConnectionTypes.Sql,
                                                ConnectorType=ConnectorTypes.POSTGRESQL,
                                                Server=ConnectionServer(Host=host, Port=port),
                                                BasicAuthentication=ConnectionBasicAuthentication(User=user, Password=password),
                                                Database=database)
        elif connector_type == ConnectorTypes.MYSQL:
            config = SqlConnectionConfiguration(ConnectionType=ConnectionTypes.Sql,
                                                ConnectorType=ConnectorTypes.MYSQL,
                                                Server=ConnectionServer(Host=host, Port=port),
                                                BasicAuthentication=ConnectionBasicAuthentication(User=user, Password=password),
                                                Database=database)
        else:
            raise Exception(f"{connector_type.name} connector type not supported")

        return self.__initialize_context(config=config)
