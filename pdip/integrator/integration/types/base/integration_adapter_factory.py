from injector import inject

from ..adapters.base import IntegrationAdapter
from ..adapters.implementation import SourceIntegration
from ..adapters.implementation import TargetIntegration
from ..domain.base import IntegrationBase
from ....dependency import IScoped
from ....exceptions import IncompatibleAdapterException


class IntegrationAdapterFactory(IScoped):
    @inject
    def __init__(self,
                 source_integration: SourceIntegration,
                 target_integration: TargetIntegration,
                 ):
        self.source_integration = source_integration
        self.target_integration = target_integration

    def get(self, integration: IntegrationBase) -> IntegrationAdapter:
        if integration.TargetConnections is None or integration.TargetConnections.ConnectionName is None:
            raise Exception(
                f"Target connection required for integration")
        elif integration.SourceConnections is None or integration.SourceConnections.ConnectionName is None:
            if isinstance(self.target_integration, IntegrationAdapter):
                return self.target_integration
            else:
                raise IncompatibleAdapterException(
                    f"{self.target_integration} is incompatible with {IntegrationAdapter}")
        else:
            if isinstance(self.source_integration, IntegrationAdapter):
                return self.source_integration
            else:
                raise IncompatibleAdapterException(
                    f"{self.source_integration} is incompatible with {IntegrationAdapter}")
