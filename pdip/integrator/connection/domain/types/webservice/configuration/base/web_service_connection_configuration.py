from dataclasses import dataclass

from pdip.integrator.connection.domain.types.webservice.configuration.soap.soap_configuration import SoapConfiguration
from pdip.integrator.connection.domain.authentication.basic import ConnectionBasicAuthentication
from pdip.integrator.connection.domain.enums import ConnectionTypes, ConnectorTypes
from pdip.integrator.connection.domain.server.base import ConnectionServer


@dataclass
class WebServiceConnectionConfiguration:
    Name: str = None
    ConnectionType: ConnectionTypes = None
    ConnectorType: ConnectorTypes = None
    Server: ConnectionServer = None
    Soap: SoapConfiguration = None
    BasicAuthentication: ConnectionBasicAuthentication = None
    Ssl: bool = False
