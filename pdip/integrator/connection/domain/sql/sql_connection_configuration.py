from typing import Optional

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from ..authentication.basic import ConnectionBasicAuthentication
from ..enums import ConnectionTypes, ConnectorTypes
from ..server.base import ConnectionServer


@dataclass_json
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
