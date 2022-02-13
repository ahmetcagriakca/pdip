from abc import abstractmethod
from typing import List

from ...integration.domain.base import IntegrationBase


class ConnectionSourceAdapter:

    @abstractmethod
    def get_source_data_count(
            self,
            integration: IntegrationBase
    ) -> int:
        pass

    @abstractmethod
    def get_source_data(
            self,
            integration: IntegrationBase
    ) -> List[any]:
        pass

    @abstractmethod
    def get_iterator(
            self,
            integration: IntegrationBase,
            limit: int
    ) -> List[any]:
        pass

    @abstractmethod
    def get_source_data_with_paging(
            self,
            integration: IntegrationBase,
            start: int,
            end: int
    ) -> List[any]:
        pass
