from injector import inject

from .web_service_context import WebServiceContext
from .web_service_policy import WebServicePolicy
from ....domain.authentication.basic import BasicAuthentication
from ....domain.enums import ConnectorTypes, ConnectionTypes
from ....domain.server.base import Server
from ....domain.webservice.base import WebServiceConnectionConfiguration
from ....domain.webservice.soap.soap_configuration import SoapConfiguration
from ......dependency import IScoped


class WebServiceProvider(IScoped):
    @inject
    def __init__(self):
        pass

    def __initialize_context(self, config: WebServiceConnectionConfiguration):
        policy = WebServicePolicy(config=config)
        context = WebServiceContext(policy=policy)
        return context

    def get_context_by_config(self, config: WebServiceConnectionConfiguration) -> WebServiceContext:
        return self.__initialize_context(config=config)

    def get_context(
            self,
            connector_type: ConnectorTypes,
            host: str, port: int,
            user: str, password: str,
            wsdl: str,
            ssl:bool=False
    ) -> WebServiceContext:
        """
        Creating Context
        """
        if connector_type == connector_type.Soap:
            config = WebServiceConnectionConfiguration(
                ConnectionType=ConnectionTypes.WebService,
                ConnectorType=ConnectorTypes.Soap,
                Server=Server(Host=host, Port=port),
                BasicAuthentication=BasicAuthentication(User=user,
                                                        Password=password),
                Soap=SoapConfiguration(Wsdl=wsdl),
                Ssl=ssl
            )
        else:
            raise Exception(f"{connector_type.name} connector type not supported")

        return self.__initialize_context(config=config)
