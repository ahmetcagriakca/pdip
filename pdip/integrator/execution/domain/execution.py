from datetime import datetime
from typing import List

from dataclasses import dataclass

from ...domain.enums import StatusTypes


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
