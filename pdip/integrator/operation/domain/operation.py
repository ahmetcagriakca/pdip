from typing import List

from dataclasses import dataclass

from ...integration.domain.base import IntegrationBase


@dataclass
class OperationIntegrationBase:
    Order: int = None
    Limit: int = None
    ProcessCount: int = None
    Integration: IntegrationBase = None

    def initialize(self):
        pass


@dataclass
class OperationBase:
    Name: str = None
    Integrations: List[OperationIntegrationBase] = None

    def initialize(self):
        pass
