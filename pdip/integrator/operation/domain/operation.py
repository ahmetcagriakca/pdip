from datetime import datetime
from typing import List

from dataclasses import dataclass

from ...domain.enums import StatusTypes
from ...integration.domain.base import IntegrationBase


@dataclass
class ExecutionBase:
    Id: int = None
    Status: StatusTypes = None
    StartDate: datetime = None
    EndDate: datetime = None


@dataclass
class EventBase:
    Id: int = None
    EventId: int = None
    EventDate: datetime = None


@dataclass
class OperationIntegrationExecutionEvent(EventBase):
    pass


@dataclass
class OperationIntegrationExecutionBase(ExecutionBase):
    Name: str = None
    OperationExecutionId: int = None
    OperationIntegrationId: int = None
    Events: List[OperationIntegrationExecutionEvent] = None


@dataclass
class OperationExecutionEvent(EventBase):
    OperationId: int = None
    Status: StatusTypes = None
    Event: int = None


@dataclass
class OperationExecutionBase(ExecutionBase):
    Name: str = None
    OperationId: int = None
    Events: List[OperationExecutionEvent] = None


@dataclass
class OperationIntegrationBase:
    Id: int = None
    Name: str = None
    Order: int = None
    Limit: int = None
    ProcessCount: int = None
    Integration: IntegrationBase = None
    Execution: OperationIntegrationExecutionBase = None


@dataclass
class OperationBase:
    Id: int = None
    Name: str = None
    Integrations: List[OperationIntegrationBase] = None
    Execution: OperationExecutionBase = None