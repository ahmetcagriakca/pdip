import importlib

from injector import inject

from pdip.integrator.connection.domain.enums import ConnectorTypes
from pdip.integrator.connection.domain.sql import SqlConnectionConfiguration
from .sql_connector import SqlConnector


class SqlPolicy:
    @inject
    def __init__(self, config: SqlConnectionConfiguration):
        self.config = config
        self.connector: SqlConnector = None
        self.connector_name = None
        sql_connector_base_module = "pdip.integrator.connection.types.sql.connectors"
        if self.config.ConnectorType == ConnectorTypes.MSSQL:
            connector_namespace = "mssql"
            connector_name = "MssqlConnector"
        elif self.config.ConnectorType == ConnectorTypes.ORACLE:
            connector_namespace = "oracle"
            connector_name = "OracleConnector"
        elif self.config.ConnectorType == ConnectorTypes.POSTGRESQL:
            connector_namespace = "postgresql"
            connector_name = "PostgresqlConnector"
        elif self.config.ConnectorType == ConnectorTypes.MYSQL:
            connector_namespace = "mysql"
            connector_name = "MysqlConnector"
        else:
            raise Exception("Connector type not found")
        module = importlib.import_module(".".join([sql_connector_base_module, connector_namespace]))
        connector_class = getattr(module, connector_name)
        if connector_class is not None:
            self.connector: SqlConnector = connector_class(self.config)
