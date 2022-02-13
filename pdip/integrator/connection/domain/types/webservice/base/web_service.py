from dataclasses import dataclass
from typing import Optional

from pdip.integrator.connection.domain.types.webservice.configuration.base.web_service_connection_configuration import WebServiceConnectionConfiguration


@dataclass
class ConnectionWebServiceBase:
    Connection: WebServiceConnectionConfiguration = None
    Method: Optional[str] = None
    RequestBody: Optional[str] = None
