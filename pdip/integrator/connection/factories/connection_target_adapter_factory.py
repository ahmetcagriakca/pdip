from injector import inject

from pdip.integrator.connection.base.connection_target_adapter import ConnectionTargetAdapter
from pdip.integrator.connection.domain.enums import ConnectionTypes
from pdip.integrator.connection.types.bigdata.adapters.target import BigDataTargetAdapter
from pdip.integrator.connection.types.sql.adapters.target import SqlTargetAdapter
from pdip.integrator.connection.types.webservice.adapters.target import WebServiceTargetAdapter
from pdip.dependency import IScoped
from pdip.exceptions import IncompatibleAdapterException, NotSupportedFeatureException


class ConnectionTargetAdapterFactory(IScoped):
    @inject
    def __init__(self,
                 sql_target_adapter: SqlTargetAdapter,
                 big_data_target_adapter: BigDataTargetAdapter,
                 web_service_target_adapter: WebServiceTargetAdapter,
                 # file_adapter: FileAdapter,
                 # queue_adapter: QueueAdapter,
                 ):
        # self.queue_adapter = queue_adapter
        # self.file_adapter = file_adapter
        self.web_service_target_adapter = web_service_target_adapter
        self.big_data_target_adapter = big_data_target_adapter
        self.sql_target_adapter = sql_target_adapter

    def get_adapter(self, connection_type: ConnectionTypes) -> ConnectionTargetAdapter:
        if connection_type == ConnectionTypes.Sql:
            if isinstance(self.sql_target_adapter, ConnectionTargetAdapter):
                return self.sql_target_adapter
            else:
                raise IncompatibleAdapterException(
                    f"{self.sql_target_adapter} is incompatible with ConnectionTargetAdapter")
        elif connection_type == ConnectionTypes.File:
            if isinstance(self.file_target_adapter, ConnectionTargetAdapter):
                return self.file_target_adapter
            else:
                raise IncompatibleAdapterException(
                    f"{self.file_target_adapter} is incompatible with ConnectionTargetAdapter")
        elif connection_type == ConnectionTypes.Queue:
            if isinstance(self.queue_target_adapter, ConnectionTargetAdapter):
                return self.queue_target_adapter
            else:
                raise IncompatibleAdapterException(
                    f"{self.queue_target_adapter} is incompatible with ConnectionTargetAdapter")
        elif connection_type == ConnectionTypes.BigData:
            if isinstance(self.big_data_target_adapter, ConnectionTargetAdapter):
                return self.big_data_target_adapter
            else:
                raise IncompatibleAdapterException(
                    f"{self.big_data_target_adapter} is incompatible with ConnectionTargetAdapter")
        elif connection_type == ConnectionTypes.WebService:
            if isinstance(self.web_service_target_adapter, ConnectionTargetAdapter):
                return self.web_service_target_adapter
            else:
                raise IncompatibleAdapterException(
                    f"{self.web_service_target_adapter} is incompatible with ConnectionTargetAdapter")
        elif connection_type == ConnectionTypes.InMemory:
            if isinstance(self.in_memory_target_adapter, ConnectionTargetAdapter):
                return self.in_memory_target_adapter
            else:
                raise IncompatibleAdapterException(
                    f"{self.in_memory_target_adapter} is incompatible with ConnectionTargetAdapter")
        else:
            raise NotSupportedFeatureException(f"{connection_type.name}")
