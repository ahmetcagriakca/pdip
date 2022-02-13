from dataclasses import dataclass
from typing import List, Optional

from ....connection.domain.base import ConnectionColumnBase
from ....connection.domain.types.bigdata.base import ConnectionBigDataBase
from ....connection.domain.enums import ConnectionTypes
from ....connection.domain.types.sql.base import ConnectionSqlBase
from ....connection.domain.types.webservice.base import ConnectionWebServiceBase


@dataclass
class IntegrationConnectionBase:
    ConnectionName: str = None
    ConnectionType: ConnectionTypes = None
    Sql: Optional[ConnectionSqlBase] = None
    BigData: Optional[ConnectionBigDataBase] = None
    WebService: Optional[ConnectionWebServiceBase] = None
    File: Optional[any] = None
    Queue: Optional[any] = None
    Columns: Optional[List[ConnectionColumnBase]] = None


@dataclass
class IntegrationBase:
    SourceConnections: Optional[IntegrationConnectionBase] = None
    TargetConnections: IntegrationConnectionBase = None
    IsTargetTruncate: Optional[bool] = None
