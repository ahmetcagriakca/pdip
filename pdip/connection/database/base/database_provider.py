from injector import inject

from .database_context import DatabaseContext
from .database_policy import DatabasePolicy
from ...models.enums import ConnectorTypes
from ....configuration.models.database import DatabaseConfig
from ....dependency import IScoped


class DatabaseProvider(IScoped):
    @inject
    def __init__(self):
        pass

    def __initialize_context(self, config: DatabaseConfig):
        database_policy = DatabasePolicy(database_config=config)
        database_context: DatabaseContext = DatabaseContext(database_policy=database_policy)
        return database_context

    def get_context_by_config(self, config: DatabaseConfig) -> DatabaseContext:
        return self.__initialize_context(config=config)

    def get_context(self, connector_type: ConnectorTypes, host, port, user, password,
                    database=None, service_name=None, sid=None) -> DatabaseContext:
        """
        Creating Context
        """
        if connector_type == connector_type.ORACLE:
            config = DatabaseConfig(type=connector_type.ORACLE.name,
                                    host=host, port=port,
                                    user=user, password=password,
                                    sid=sid, service_name=service_name)
        elif connector_type == connector_type.MSSQL:
            config = DatabaseConfig(type=connector_type.MSSQL.name,
                                    host=host, port=port,
                                    user=user, password=password,
                                    database=database)
        elif connector_type == connector_type.POSTGRESQL:
            config = DatabaseConfig(type=connector_type.POSTGRESQL.name,
                                    host=host, port=port,
                                    user=user, password=password,
                                    database=database)
        elif connector_type == connector_type.MYSQL:
            config = DatabaseConfig(type=connector_type.MYSQL.name,
                                    host=host, port=port,
                                    user=user, password=password,
                                    database=database)
        else:
            raise Exception(f"{connector_type.name} connector type not supported")

        return self.__initialize_context(config=config)
