from abc import ABC, abstractmethod

from pdip.integrator.operation.domain import OperationIntegrationBase
from pdip.integrator.pubsub.base import ChannelQueue


class AsyncIntegrationExecute(ABC):
    """Async sibling of
    :class:`IntegrationSourceToTargetExecuteStrategy` (ADR-0032 §4).

    Concrete implementations live under ``async_/<flavour>/`` and
    require the ``pdip[async]`` extra. The class is registered with
    :class:`IntegrationSourceToTargetExecuteStrategyFactory` via the
    ``is_async`` flag once a concrete async strategy is wired in;
    until then the factory raises
    :class:`NotSupportedFeatureException` for ``is_async=True``.
    """

    @abstractmethod
    async def execute(
            self,
            operation_integration: OperationIntegrationBase,
            channel: ChannelQueue
    ) -> int:
        pass
