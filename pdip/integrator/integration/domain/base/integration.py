from typing import List, Optional

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from ....connection.domain.bigdata import BigDataConnectionConfiguration
from ....connection.domain.enums import ConnectionTypes
from ....connection.domain.inmemory import InMemoryConnectionConfiguration
from ....connection.domain.sql import SqlConnectionConfiguration
from ....connection.domain.webservice.base import WebServiceConnectionConfiguration


@dataclass_json
@dataclass
class IntegrationConnectionInMemoryDataBase:
    Connection: InMemoryConnectionConfiguration = None
    Schema: Optional[str] = None
    ObjectName: Optional[str] = None
    Query: Optional[str] = None


@dataclass_json
@dataclass
class IntegrationConnectionWebServiceBase:
    Connection: WebServiceConnectionConfiguration = None
    Method: Optional[str] = None
    RequestBody: Optional[str] = None


@dataclass_json
@dataclass
class IntegrationConnectionBigDataBase:
    Connection: BigDataConnectionConfiguration = None
    Schema: Optional[str] = None
    ObjectName: Optional[str] = None
    Query: Optional[str] = None


@dataclass_json
@dataclass
class IntegrationConnectionSqlBase:
    Connection: SqlConnectionConfiguration = None
    Schema: Optional[str] = None
    ObjectName: Optional[str] = None
    Query: Optional[str] = None


@dataclass_json
@dataclass
class IntegrationConnectionColumnBase:
    Name: str = None
    Type: Optional[str] = None


@dataclass_json
@dataclass
class IntegrationConnectionBase:
    ConnectionName: str = None
    ConnectionType: ConnectionTypes = None
    Sql: Optional[IntegrationConnectionSqlBase] = None
    BigData: Optional[IntegrationConnectionBigDataBase] = None
    WebService: Optional[IntegrationConnectionWebServiceBase] = None
    File: Optional[any] = None
    Queue: Optional[any] = None
    Columns: Optional[List[IntegrationConnectionColumnBase]] = None


@dataclass_json
@dataclass
class IntegrationBase:
    SourceConnections: Optional[IntegrationConnectionBase] = None
    TargetConnections: IntegrationConnectionBase = None
    IsTargetTruncate: Optional[bool] = None
