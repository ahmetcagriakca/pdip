from injector import inject

from pdip.dependency import IScoped
from pdip.exceptions import IncompatibleAdapterException
from pdip.integrator.integration.types.sourcetotarget.strategies import IntegrationSourceToTargetExecuteStrategy, \
    ParallelIntegrationExecute, SingleProcessIntegrationExecute


class IntegrationSourceToTargetExecuteStrategyFactory(IScoped):
    @inject
    def __init__(self,
                 parallel_integration_execute: ParallelIntegrationExecute,
                 single_process_integration_execute: SingleProcessIntegrationExecute,
                 ):
        self.single_process_integration_execute = single_process_integration_execute
        self.parallel_integration_execute = parallel_integration_execute

    def get(self, process_count: int) -> IntegrationSourceToTargetExecuteStrategy:
        if process_count is not None and process_count > 1:
            if isinstance(self.parallel_integration_execute, IntegrationSourceToTargetExecuteStrategy):
                return self.parallel_integration_execute
            else:
                raise IncompatibleAdapterException(
                    f"{self.execute_integration_adapter} is incompatible with {IntegrationSourceToTargetExecuteStrategy}")
        else:
            if isinstance(self.single_process_integration_execute, IntegrationSourceToTargetExecuteStrategy):
                return self.single_process_integration_execute
            else:
                raise IncompatibleAdapterException(
                    f"{self.single_process_integration_execute} is incompatible with {IntegrationSourceToTargetExecuteStrategy}")
