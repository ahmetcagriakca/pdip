from abc import abstractmethod
from typing import List

from ...integration.domain.base import IntegrationBase


class AsyncConnectionTargetAdapter:
    """Async sibling of :class:`ConnectionTargetAdapter` (ADR-0032 §3).

    Concrete implementations live next to their sync siblings under
    ``pdip/integrator/connection/types/`` and become available when
    ``pdip[async]`` is installed. The sync class is unchanged.
    """

    async def clear_data(
            self,
            integration: IntegrationBase
    ) -> int:
        pass

    @abstractmethod
    async def write_data(
            self,
            integration: IntegrationBase,
            source_data: List[any]
    ) -> int:
        pass

    @abstractmethod
    async def do_target_operation(
            self,
            integration: IntegrationBase
    ) -> int:
        pass
