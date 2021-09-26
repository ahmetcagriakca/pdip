import importlib

from injector import inject

from .connectors.DatabaseConnector import DatabaseConnector
from ..models.enums import ConnectorTypes
from ...configuration.models.database_config import DatabaseConfig


class DatabasePolicy:
    @inject
    def __init__(self, database_config: DatabaseConfig):
        self.database_config = database_config
        self.connector: DatabaseConnector = None
        self.connector_name = None
        database_connector_base_module = "pdip.connection.database.connectors"
        if database_config.type == ConnectorTypes.MSSQL.name:
            connector_name = "MssqlDbConnector"
        elif database_config.type == ConnectorTypes.ORACLE.name:
            connector_name = "OracleDbConnector"
        elif database_config.type == ConnectorTypes.POSTGRESQL.name:
            connector_name = "PostgreDbConnector"
        elif database_config.type == ConnectorTypes.MYSQL.name:
            connector_name = "MssqlDbConnector"
        else:
            raise Exception("Connector type not found")
        module = importlib.import_module(".".join([database_connector_base_module, connector_name]))
        connector_class = getattr(module, connector_name)
        if connector_class is not None:
            self.connector: DatabaseConnector = connector_class(database_config)
