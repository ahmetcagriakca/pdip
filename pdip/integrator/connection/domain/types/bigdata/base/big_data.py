from dataclasses import dataclass
from typing import Optional

from pdip.integrator.connection.domain.types.bigdata.configuration import BigDataConnectionConfiguration


@dataclass
class ConnectionBigDataBase:
    Connection: BigDataConnectionConfiguration = None
    Schema: Optional[str] = None
    ObjectName: Optional[str] = None
    Query: Optional[str] = None
