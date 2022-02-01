from injector import inject

from pdip.dependency import IScoped
from pdip.exceptions import IncompatibleAdapterException
from pdip.integrator.integration.domain.base import IntegrationBase
from pdip.integrator.integration.types.base import IntegrationAdapter
from pdip.integrator.integration.types.source.base.source_integration import SourceIntegration
from pdip.integrator.integration.types.sourcetotarget.base import SourceToTargetIntegration
from pdip.integrator.integration.types.target.base import TargetIntegration


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
