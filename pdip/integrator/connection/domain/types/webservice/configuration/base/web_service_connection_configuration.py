from dataclasses import dataclass

from ..soap import SoapConfiguration
from .....authentication.basic import ConnectionBasicAuthentication
from .....enums import ConnectionTypes, ConnectorTypes
from .....server.base import ConnectionServer


@dataclass
class WebServiceConnectionConfiguration:
    Name: str = None
    ConnectionType: ConnectionTypes = None
    ConnectorType: ConnectorTypes = None
    Server: ConnectionServer = None
    Soap: SoapConfiguration = None
    BasicAuthentication: ConnectionBasicAuthentication = None
    Ssl: bool = False
