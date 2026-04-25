from injector import inject

from ..base import ConnectionTargetAdapter
from ..base._async_extra import require_async_extra
from ..domain.enums import ConnectionTypes
from ..types.bigdata.adapters.target import BigDataTargetAdapter
from ..types.sql.adapters.target import SqlTargetAdapter
from ..types.webservice.adapters.target import WebServiceTargetAdapter
from ....dependency import IScoped
from ....exceptions import IncompatibleAdapterException, NotSupportedFeatureException


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

    def get_adapter(
            self,
            connection_type: ConnectionTypes,
            is_async: bool = False,
    ) -> ConnectionTargetAdapter:
        if is_async:
            require_async_extra()
            raise NotSupportedFeatureException(
                f"async {connection_type.name} target adapter is not yet "
                f"wired in this build (see ADR-0032 follow-ups)"
            )
        if connection_type == ConnectionTypes.Sql:
            if isinstance(self.sql_target_adapter, ConnectionTargetAdapter):
                return self.sql_target_adapter
            else:
                raise IncompatibleAdapterException(
                    f"{self.sql_target_adapter} is incompatible with ConnectionTargetAdapter")
        elif connection_type == ConnectionTypes.File:
            raise NotSupportedFeatureException(
                f"{connection_type.name} target adapter is not wired in this build")
        elif connection_type == ConnectionTypes.Queue:
            raise NotSupportedFeatureException(
                f"{connection_type.name} target adapter is not wired in this build")
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
            raise NotSupportedFeatureException(
                f"{connection_type.name} target adapter is not wired in this build")
        else:
            raise NotSupportedFeatureException(f"{connection_type.name}")
