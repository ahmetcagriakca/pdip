from dataclasses import dataclass
from typing import Optional

from ..configuration.base import BigDataConnectionConfiguration


@dataclass
class ConnectionBigDataBase:
    Connection: BigDataConnectionConfiguration = None
    Schema: Optional[str] = None
    ObjectName: Optional[str] = None
    Query: Optional[str] = None
