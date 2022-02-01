import importlib

from injector import inject

from .sql_connector import SqlConnector
from .sql_dialect import SqlDialect
from ....domain.enums import ConnectorTypes
from ....domain.sql import SqlConnectionConfiguration


class SqlPolicy:
    @inject
    def __init__(self, config: SqlConnectionConfiguration):
        self.config = config
        self.connector: SqlConnector = None
        self.connector_name = None
        connector_base_module = "pdip.integrator.connection.types.sql.connectors"
        dialect_base_module = "pdip.integrator.connection.types.sql.dialects"
        if self.config.ConnectorType == ConnectorTypes.MSSQL:
            namespace = "mssql"
            connector_name = "MssqlConnector"
            dialect_name = "MssqlDialect"
        elif self.config.ConnectorType == ConnectorTypes.ORACLE:
            namespace = "oracle"
            connector_name = "OracleConnector"
            dialect_name = "OracleDialect"
        elif self.config.ConnectorType == ConnectorTypes.POSTGRESQL:
            namespace = "postgresql"
            connector_name = "PostgresqlConnector"
            dialect_name = "PostgresqlDialect"
        elif self.config.ConnectorType == ConnectorTypes.MYSQL:
            namespace = "mysql"
            connector_name = "MysqlConnector"
            dialect_name = "MysqlDialect"
        else:
            raise Exception("Connector type not found")
        module = importlib.import_module(".".join([connector_base_module, namespace]))
        connector_class = getattr(module, connector_name)
        if connector_class is not None:
            self.connector: SqlConnector = connector_class(self.config)
        module = importlib.import_module(".".join([dialect_base_module, namespace]))
        dialect_class = getattr(module, dialect_name)
        if dialect_class is not None:
            self.dialect: SqlDialect = dialect_class(self.connector)
