from dataclasses import dataclass

from ..authentication.basic import BasicAuthentication
from ..enums import ConnectionTypes, ConnectorTypes
from ..server.base import Server


@dataclass
class SqlConnectionConfiguration:
    Name: str = None
    ConnectionType: ConnectionTypes = None
    ConnectorType: ConnectorTypes = None
    ConnectionString: str = None
    Driver: str = None
    Server: Server = None
    Sid: str = None
    ServiceName: str = None
    Database: str = None
    BasicAuthentication: BasicAuthentication = None
    application_name: str = None
    execution_options: str = None
