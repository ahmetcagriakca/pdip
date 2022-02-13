from abc import abstractmethod
from typing import List

from ...integration.domain.base import IntegrationBase


class ConnectionTargetAdapter:
    def clear_data(
            self,
            integration: IntegrationBase
    ) -> int:
        pass

    @abstractmethod
    def write_target_data(
            self,
            integration: IntegrationBase,
            source_data: List[any]
    ) -> int:
        pass

    @abstractmethod
    def do_target_operation(
            self,
            integration: IntegrationBase
    ) -> int:
        pass
