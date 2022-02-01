from injector import inject

from ..base import ConnectionSourceAdapter
from ..domain.enums import ConnectionTypes
from ..types.bigdata.adapters.source import BigDataSourceAdapter
from ..types.sql.adapters.source import SqlSourceAdapter
from ..types.webservice.adapters.source import WebServiceSourceAdapter
from ....dependency import IScoped
from ....exceptions import IncompatibleAdapterException, NotSupportedFeatureException


class ConnectionSourceAdapterFactory(IScoped):
    @inject
    def __init__(self,
                 sql_source_adapter: SqlSourceAdapter,
                 big_data_source_adapter: BigDataSourceAdapter,
                 web_service_source_adapter: WebServiceSourceAdapter,
                 # file_adapter: FileAdapter,
                 # queue_adapter: QueueAdapter,
                 ):
        # self.queue_adapter = queue_adapter
        # self.file_adapter = file_adapter
        self.web_service_source_adapter = web_service_source_adapter
        self.big_data_source_adapter = big_data_source_adapter
        self.sql_source_adapter = sql_source_adapter

    def get_adapter(self, connection_type: ConnectionTypes) -> ConnectionSourceAdapter:
        if connection_type == ConnectionTypes.Sql:
            if isinstance(self.sql_source_adapter, ConnectionSourceAdapter):
                return self.sql_source_adapter
            else:
                raise IncompatibleAdapterException(
                    f"{self.sql_source_adapter} is incompatible with ConnectionSourceAdapter")
        elif connection_type == ConnectionTypes.File:
            if isinstance(self.file_source_adapter, ConnectionSourceAdapter):
                return self.file_source_adapter
            else:
                raise IncompatibleAdapterException(
                    f"{self.file_source_adapter} is incompatible with ConnectionSourceAdapter")
        elif connection_type == ConnectionTypes.Queue:
            if isinstance(self.queue_source_adapter, ConnectionSourceAdapter):
                return self.queue_source_adapter
            else:
                raise IncompatibleAdapterException(
                    f"{self.queue_source_adapter} is incompatible with ConnectionSourceAdapter")
        elif connection_type == ConnectionTypes.BigData:
            if isinstance(self.big_data_source_adapter, ConnectionSourceAdapter):
                return self.big_data_source_adapter
            else:
                raise IncompatibleAdapterException(
                    f"{self.big_data_source_adapter} is incompatible with ConnectionSourceAdapter")
        elif connection_type == ConnectionTypes.WebService:
            if isinstance(self.web_service_source_adapter, ConnectionSourceAdapter):
                return self.web_service_source_adapter
            else:
                raise IncompatibleAdapterException(
                    f"{self.web_service_source_adapter} is incompatible with ConnectionSourceAdapter")
        else:
            raise NotSupportedFeatureException(f"{connection_type.name}")
