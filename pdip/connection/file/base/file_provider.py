import os

from injector import inject

from .file_connector import FileConnector
from .file_context import FileContext
from ..connectors.csv import CsvConnector
from ...models.enums import ConnectorTypes
from ....configuration.models.application import ApplicationConfig
from ....dependency import IScoped
from ....logging.loggers.database import SqlLogger


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
        connector: FileConnector = None
        if connection.File.ConnectorType.Name == ConnectorTypes.CSV.name:
            host = connection_server.Host
            port = connection_server.Port
            if host is None or host == '':
                host = os.path.join(self.application_config.root_directory, "files")
            if connection.File.ConnectorType.Name == ConnectorTypes.CSV.name:
                connector = CsvConnector(host=host)
        if connector is not None:
            file_context: FileContext = FileContext(connector=connector)
            return file_context
        else:
            raise Exception(f"{connection.File.ConnectorType.Name} connector type not supported")

    def get_file_context_with_host(self, host: str) -> FileContext:
        """
        Creating Connection
        """
        if host is None or host == '':
            host = os.path.join(self.application_config.root_directory, "files")
        connector = CsvConnector(folder=host)
        file_context: FileContext = FileContext(connector=connector)
        return file_context
