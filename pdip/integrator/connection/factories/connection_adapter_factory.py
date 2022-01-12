from injector import inject

from ..adapters import SqlAdapter, BigDataAdapter, WebServiceAdapter  # , FileAdapter, QueueAdapter
from ..base import ConnectionAdapter
from ..domain.enums import ConnectionTypes
from ....dependency import IScoped
from ....exceptions import IncompatibleAdapterException, NotSupportedFeatureException


class ConnectionAdapterFactory(IScoped):
    @inject
    def __init__(self,
                 sql_adapter: SqlAdapter,
                 big_data_adapter: BigDataAdapter,
                 web_service_adapter: WebServiceAdapter,
                 # file_adapter: FileAdapter,
                 # queue_adapter: QueueAdapter,
                 ):
        # self.queue_adapter = queue_adapter
        # self.file_adapter = file_adapter
        self.web_service_adapter = web_service_adapter
        self.big_data_adapter = big_data_adapter
        self.sql_adapter = sql_adapter

    def get_adapter(self, connection_type: ConnectionTypes) -> ConnectionAdapter:
        if connection_type == ConnectionTypes.Sql:
            if isinstance(self.sql_adapter, ConnectionAdapter):
                return self.sql_adapter
            else:
                raise IncompatibleAdapterException(f"{self.sql_adapter} is incompatible with ConectionAdapter")
        elif connection_type == ConnectionTypes.File:
            if isinstance(self.file_adapter, ConnectionAdapter):
                return self.file_adapter
            else:
                raise IncompatibleAdapterException(f"{self.file_adapter} is incompatible with ConectionAdapter")
        elif connection_type == ConnectionTypes.Queue:
            if isinstance(self.queue_adapter, ConnectionAdapter):
                return self.queue_adapter
            else:
                raise IncompatibleAdapterException(f"{self.queue_adapter} is incompatible with ConectionAdapter")
        elif connection_type == ConnectionTypes.BigData:
            if isinstance(self.big_data_adapter, ConnectionAdapter):
                return self.big_data_adapter
            else:
                raise IncompatibleAdapterException(f"{self.big_data_adapter} is incompatible with ConectionAdapter")
        elif connection_type == ConnectionTypes.WebService:
            if isinstance(self.web_service_adapter, ConnectionAdapter):
                return self.web_service_adapter
            else:
                raise IncompatibleAdapterException(f"{self.web_service_adapter} is incompatible with ConectionAdapter")
        else:
            raise NotSupportedFeatureException(f"{connection_type.name}")
