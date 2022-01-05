from datetime import datetime
from typing import List

from dataclasses import dataclass

from ...domain.enums import StatusTypes
from ...integration.domain.base import IntegrationBase


@dataclass
class ExecutionBase:
    Id: int = None
    ApSchedulerJobId: int = None
    Status: StatusTypes = None
    StartDate: datetime = None
    EndDate: datetime = None


@dataclass
class EventBase:
    Id: int = None
    EventId: int = None
    EventDate: datetime = None


@dataclass
class ExecutionOperationIntegrationEvent(EventBase):
    pass


@dataclass
class ExecutionOperationIntegrationBase(ExecutionBase):
    Name: str = None
    OperationId: int = None
    OperationExecutionId: int = None
    OperationIntegrationId: int = None
    Events: List[ExecutionOperationIntegrationEvent] = None


@dataclass
class ExecutionOperationEvent(EventBase):
    OperationId: int = None
    Status: StatusTypes = None
    Event: int = None


@dataclass
class ExecutionOperationBase(ExecutionBase):
    Name: str = None
    OperationId: int = None
    Events: List[ExecutionOperationEvent] = None


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
