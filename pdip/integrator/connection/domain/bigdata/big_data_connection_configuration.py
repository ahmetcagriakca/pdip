from dataclasses import dataclass

from ..authentication.basic import ConnectionBasicAuthentication
from ..authentication.kerberos import KerberosAuthentication
from ..authentication.mechanism import MechanismTypes
from ..enums import ConnectionTypes
from ..server.base import ConnectionServer
from ...domain.enums import ConnectorTypes


@dataclass
class BigDataConnectionConfiguration:
    Name: str = None
    ConnectionString: str = None
    ConnectionType: ConnectionTypes = None
    ConnectorType: ConnectorTypes = None
    Driver: str = None
    Server: ConnectionServer = None
    Database: str = None
    BasicAuthentication: ConnectionBasicAuthentication = None
    KerberosAuthentication: KerberosAuthentication = None
    AuthenticationMechanismType: MechanismTypes = None
    Ssl: bool = None
    UseOnlySspi: bool = None
    ApplicationName: str = None
