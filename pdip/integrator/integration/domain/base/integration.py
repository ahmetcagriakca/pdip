from typing import List

from dataclasses import dataclass

from ....connection.domain.bigdata import BigDataConnectionConfiguration
from ....connection.domain.enums import ConnectionTypes
from ....connection.domain.sql import SqlConnectionConfiguration
from ....connection.domain.webservice.base import WebServiceConnectionConfiguration


@dataclass
class IntegrationConnectionWebServiceBase:
    Connection: WebServiceConnectionConfiguration = None
    Method: str = None
    RequestBody: str = None


@dataclass
class IntegrationConnectionBigDataBase:
    Connection: BigDataConnectionConfiguration = None
    Schema: str = None
    ObjectName: str = None
    Query: str = None


@dataclass
class IntegrationConnectionSqlBase:
    Connection: SqlConnectionConfiguration = None
    Schema: str = None
    ObjectName: str = None
    Query: str = None


@dataclass
class IntegrationConnectionColumnBase:
    Name: str = None
    Type: str = None


@dataclass
class IntegrationConnectionBase:
    ConnectionName: str = None
    ConnectionType: ConnectionTypes = None
    Sql: IntegrationConnectionSqlBase = None
    BigData: IntegrationConnectionBigDataBase = None
    WebService: IntegrationConnectionWebServiceBase = None
    File: any = None
    Queue: any = None
    Columns: List[IntegrationConnectionColumnBase] = None


@dataclass
class IntegrationBase:
    SourceConnections: IntegrationConnectionBase = None
    TargetConnections: IntegrationConnectionBase = None
    IsTargetTruncate: bool = None
