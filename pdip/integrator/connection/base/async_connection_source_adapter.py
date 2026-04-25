from abc import abstractmethod
from typing import List

from ...integration.domain.base import IntegrationBase


class AsyncConnectionSourceAdapter:
    """Async sibling of :class:`ConnectionSourceAdapter` (ADR-0032 §3).

    Concrete implementations live next to their sync siblings under
    ``pdip/integrator/connection/types/`` and become available when
    ``pdip[async]`` is installed. The sync class is unchanged.
    """

    @abstractmethod
    async def get_source_data_count(
            self,
            integration: IntegrationBase
    ) -> int:
        pass

    @abstractmethod
    async def get_iterator(
            self,
            integration: IntegrationBase,
            limit: int
    ) -> List[any]:
        pass

    @abstractmethod
    async def get_source_data_with_paging(
            self,
            integration: IntegrationBase,
            start: int,
            end: int
    ) -> List[any]:
        pass
