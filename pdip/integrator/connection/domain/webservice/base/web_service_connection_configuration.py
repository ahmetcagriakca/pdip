from dataclasses import dataclass

from ..soap.soap_configuration import SoapConfiguration
from ....domain.authentication.basic import ConnectionBasicAuthentication
from ....domain.enums import ConnectionTypes, ConnectorTypes
from ....domain.server.base import ConnectionServer


@dataclass
class WebServiceConnectionConfiguration:
    Name: str = None
    ConnectionType: ConnectionTypes = None
    ConnectorType: ConnectorTypes = None
    Server: ConnectionServer = None
    Soap: SoapConfiguration = None
    BasicAuthentication: ConnectionBasicAuthentication = None
    Ssl: bool = False
