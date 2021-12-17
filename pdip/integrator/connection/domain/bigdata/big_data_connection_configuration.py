from dataclasses import dataclass

from ..authentication.basic import BasicAuthentication
from ..authentication.kerberos import KerberosAuthentication
from ..authentication.mechanism import MechanismTypes
from ..enums import ConnectionTypes
from ..server.base import Server
from ...domain.enums import ConnectorTypes


@dataclass
class BigDataConnectionConfiguration:
    Name: str = None
    ConnectionString: str = None
    ConnectionType: ConnectionTypes = None
    ConnectorType: ConnectorTypes = None
    Driver: str = None
    Server: Server = None
    Database: str = None
    BasicAuthentication: BasicAuthentication = None
    KerberosAuthentication: KerberosAuthentication = None
    AuthenticationMechanismType: MechanismTypes = None
    Ssl: bool = None
    UseOnlySspi: bool = None
    ApplicationName: str = None
