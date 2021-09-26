from injector import inject

from .DatabaseContext import DatabaseContext
from .DatabasePolicy import DatabasePolicy
from ..models.enums import ConnectionTypes, ConnectorTypes
from ...dependency import IScoped
from ...configuration.models import DatabaseConfig


class DatabaseProvider(IScoped):
    @inject
    def __init__(self,
                 ):
        pass

    def get_context(self, connection_type: ConnectionTypes, connector_type: ConnectorTypes, host, port, user, password,
                    database=None, service_name=None, sid=None) -> DatabaseContext:
        """
        Creating Database Context
        """
        if connection_type == ConnectionTypes.Database:
            if connector_type == connector_type.ORACLE:
                config = DatabaseConfig(type=connector_type.ORACLE.name, host=host, port=port,
                                        sid=sid, service_name=service_name, username=user, password=password)
            elif connector_type == connector_type.MSSQL:
                config = DatabaseConfig(type=connector_type.MSSQL.name, host=host, port=port,
                                        database=database, username=user, password=password)
            elif connector_type == connector_type.POSTGRESQL:
                config = DatabaseConfig(type=connector_type.POSTGRESQL.name, host=host, port=port,
                                        database=database, username=user, password=password)
            elif connector_type == connector_type.MYSQL:
                config = DatabaseConfig(type=connector_type.MYSQL.name, host=host, port=port,
                                        database=database, username=user, password=password)
            else:
                raise Exception(f"{connector_type.name} connector type not supported")

            database_policy = DatabasePolicy(database_config=config)
            database_context: DatabaseContext = DatabaseContext(database_policy=database_policy)
            return database_context
        else:
            raise Exception(f"{connection_type.name} connection type not supported")
