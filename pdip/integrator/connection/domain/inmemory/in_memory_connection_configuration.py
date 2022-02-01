from dataclasses import dataclass

from pdip.integrator.connection.domain.enums import ConnectionTypes, ConnectorTypes


@dataclass
class InMemoryConnectionConfiguration:
    Name: str = None
    ConnectionString: str = None
    ConnectionType: ConnectionTypes = None
    ConnectorType: ConnectorTypes = None
    Database: str = None
