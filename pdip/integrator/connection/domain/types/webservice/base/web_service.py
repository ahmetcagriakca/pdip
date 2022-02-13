from dataclasses import dataclass
from typing import Optional

from ..configuration.base import WebServiceConnectionConfiguration


@dataclass
class ConnectionWebServiceBase:
    Connection: WebServiceConnectionConfiguration = None
    Method: Optional[str] = None
    RequestBody: Optional[str] = None
