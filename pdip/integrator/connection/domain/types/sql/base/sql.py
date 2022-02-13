from dataclasses import dataclass
from typing import Optional

from ..configuration.base import SqlConnectionConfiguration


@dataclass
class ConnectionSqlBase:
    Connection: SqlConnectionConfiguration = None
    Schema: Optional[str] = None
    ObjectName: Optional[str] = None
    Query: Optional[str] = None
