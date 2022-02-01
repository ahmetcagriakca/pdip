from injector import inject

from pdip.dependency import IScoped
from pdip.exceptions import IncompatibleAdapterException
from pdip.integrator.integration.types.sourcetotarget.strategies import IntegrationSourceToTargetExecuteStrategy, \
    LimitOffIntegrationExecute, ParallelIntegrationExecute, SingleProcessIntegrationExecute


class IntegrationSourceToTargetExecuteStrategyFactory(IScoped):
    @inject
    def __init__(self,
                 limit_off_integration_execute: LimitOffIntegrationExecute,
                 parallel_integration_execute: ParallelIntegrationExecute,
                 single_process_integration_execute: SingleProcessIntegrationExecute,
                 ):
        self.single_process_integration_execute = single_process_integration_execute
        self.parallel_integration_execute = parallel_integration_execute
        self.limit_off_integration_execute = limit_off_integration_execute

    def get(self, limit: int, process_count: int) -> IntegrationSourceToTargetExecuteStrategy:
        if limit is None or limit == 0:
            if isinstance(self.limit_off_integration_execute, IntegrationSourceToTargetExecuteStrategy):
                return self.limit_off_integration_execute
            else:
                raise IncompatibleAdapterException(
                    f"{self.limit_off_integration_execute} is incompatible with {IntegrationSourceToTargetExecuteStrategy}")
        elif process_count is not None and process_count > 1:
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
