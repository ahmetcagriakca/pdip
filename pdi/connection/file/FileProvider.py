import os

from injector import inject

from .FileContext import FileContext
from .connectors.CsvConnector import CsvConnector
from .connectors.FileConnector import FileConnector
from ...dependency import IScoped
from pdi.logging.loggers.database.sql_logger import SqlLogger
from ...configuration.models.application_config import ApplicationConfig
from ..models.enums import connection_types, connector_types


class FileProvider(IScoped):
    @inject
    def __init__(self,
                 sql_logger: SqlLogger,
                 application_config: ApplicationConfig
                 ):
        self.application_config = application_config
        self.sql_logger = sql_logger

    def get_context(self, connection, connection_basic_authentication, connection_server) -> FileContext:
        """
        Creating Connection
        """
        if connection.ConnectionType.Name == connection_types.File.name:
            connector: FileConnector = None
            if connection.File.ConnectorType.Name == connector_types.CSV.name:
                host = connection_server.Host
                port = connection_server.Port
                if host is None or host == '':
                    host = os.path.join(self.application_config.root_directory, "files")
                if connection.File.ConnectorType.Name == connector_types.CSV.name:
                    connector = CsvConnector(host=host)
            if connector is not None:
                file_context: FileContext = FileContext(connector=connector)
                return file_context
            else:
                raise Exception(f"{connection.File.ConnectorType.Name} connector type not supported")

        else:
            raise Exception(f"{connection.ConnectionType.Name} connection type not supported")

    def get_file_context_with_host(self, host: str) -> FileContext:
        """
        Creating Connection
        """

        if host is None or host == '':
            host = os.path.join(self.application_config.root_directory, "files")
        connector = CsvConnector(folder=host)
        file_context: FileContext = FileContext(connector=connector)
        return file_context
