from typing import List

from dataclasses import dataclass

from ...execution.domain import ExecutionOperationIntegrationBase, ExecutionOperationBase
from ...integration.domain.base import IntegrationBase


@dataclass
class OperationIntegrationBase:
    Id: int = None
    Name: str = None
    Order: int = None
    Limit: int = None
    ProcessCount: int = None
    Integration: IntegrationBase = None
    Execution: ExecutionOperationIntegrationBase = None


@dataclass
class OperationBase:
    Id: int = None
    Name: str = None
    Integrations: List[OperationIntegrationBase] = None
    Execution: ExecutionOperationBase = None
