from dataclasses import dataclass

from pdip.integrator.connection.domain.authentication.basic import ConnectionBasicAuthentication
from pdip.integrator.connection.domain.authentication.kerberos import KerberosAuthentication
from pdip.integrator.connection.domain.authentication.mechanism import MechanismTypes
from pdip.integrator.connection.domain.enums import ConnectionTypes
from pdip.integrator.connection.domain.server.base import ConnectionServer
from pdip.integrator.connection.domain.enums import ConnectorTypes


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
