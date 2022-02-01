from injector import inject

from ...domain.base import IntegrationBase
from ...types.base import IntegrationAdapter
from ...types.source.base import SourceIntegration
from ...types.sourcetotarget.base import SourceToTargetIntegration
from ...types.target.base import TargetIntegration
from .....dependency import IScoped
from .....exceptions import IncompatibleAdapterException


class IntegrationAdapterFactory(IScoped):
    @inject
    def __init__(self,
                 source_integration: SourceIntegration,
                 target_integration: TargetIntegration,
                 source_to_target_integration: SourceToTargetIntegration,
                 ):
        self.source_to_target_integration = source_to_target_integration
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
                return self.source_to_target_integration
            else:
                raise IncompatibleAdapterException(
                    f"{self.source_integration} is incompatible with {IntegrationAdapter}")
