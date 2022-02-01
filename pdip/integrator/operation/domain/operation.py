from typing import List, Optional

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from ...execution.domain import ExecutionOperationIntegrationBase, ExecutionOperationBase
from ...integration.domain.base import IntegrationBase


@dataclass_json
@dataclass
class OperationIntegrationBase:
    Id: Optional[int] = None
    Name: str = None
    Order: int = None
    Limit: Optional[int] = None
    ProcessCount: Optional[int] = None
    Integration: IntegrationBase = None
    Execution: Optional[ExecutionOperationIntegrationBase] = None


@dataclass_json
@dataclass
class OperationBase:
    Id: Optional[int] = None
    Name: str = None
    Integrations: List[OperationIntegrationBase] = None
    Execution: Optional[ExecutionOperationBase] = None
