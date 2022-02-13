from dataclasses import dataclass
from typing import Optional

from pdip.integrator.connection.domain.authentication.basic import ConnectionBasicAuthentication
from pdip.integrator.connection.domain.enums import ConnectionTypes, ConnectorTypes
from pdip.integrator.connection.domain.server.base import ConnectionServer


@dataclass
class SqlConnectionConfiguration:
    Name: str = None
    ConnectionType: ConnectionTypes = None
    ConnectorType: ConnectorTypes = None
    ConnectionString: Optional[str] = None
    Driver: Optional[str] = None
    Server: ConnectionServer = None
    Sid: Optional[str] = None
    ServiceName: Optional[str] = None
    Database: Optional[str] = None
    BasicAuthentication: ConnectionBasicAuthentication = None
    ApplicationName: Optional[str] = None
    ExecutionOptions: Optional[str] = None
