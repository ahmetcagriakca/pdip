from dataclasses import dataclass

from ..soap.soap_configuration import SoapConfiguration
from ....domain.authentication.basic import BasicAuthentication
from ....domain.enums import ConnectionTypes, ConnectorTypes
from ....domain.server.base import Server


@dataclass
class WebServiceConnectionConfiguration:
    Name: str = None
    ConnectionType: ConnectionTypes = None
    ConnectorType: ConnectorTypes = None
    Server: Server = None
    Soap: SoapConfiguration = None
    BasicAuthentication: BasicAuthentication = None
    Ssl: bool = False
