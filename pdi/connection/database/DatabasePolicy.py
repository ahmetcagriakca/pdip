from injector import inject
from infrastructure.connection.database.connectors.DatabaseConnector import DatabaseConnector
from infrastructure.connection.database.connectors.MssqlDbConnector import MssqlDbConnector
from infrastructure.connection.database.connectors.OracleDbConnector import OracleDbConnector
from infrastructure.connection.database.connectors.PostgreDbConnector import PostgreDbConnector
from infrastructure.connection.database.connectors.MysqlDbConnector import MysqlDbConnector
from models.configs.DatabaseConfig import DatabaseConfig
from models.enums import ConnectorTypes


class DatabasePolicy:
    @inject
    def __init__(self, database_config: DatabaseConfig):
        self.database_config = database_config
        self.connector: DatabaseConnector = None
        if database_config.type == ConnectorTypes.MSSQL.name:
            self.connector: DatabaseConnector = MssqlDbConnector(database_config)
        elif database_config.type == ConnectorTypes.ORACLE.name:
            self.connector: DatabaseConnector = OracleDbConnector(database_config)
        elif database_config.type == ConnectorTypes.POSTGRESQL.name:
            self.connector: DatabaseConnector = PostgreDbConnector(database_config)
        elif database_config.type == ConnectorTypes.MYSQL.name:
            self.connector: DatabaseConnector = MysqlDbConnector(database_config)