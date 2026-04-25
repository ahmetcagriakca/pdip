from injector import inject

from ..base import IntegrationSourceToTargetExecuteStrategy
from ..parallelthread.base import ParallelThreadIntegrationExecute
from ..singleprocess.base import SingleProcessIntegrationExecute
from .......dependency import IScoped
from .......exceptions import (
    IncompatibleAdapterException,
    NotSupportedFeatureException,
)


class IntegrationSourceToTargetExecuteStrategyFactory(IScoped):
    @inject
    def __init__(self,
                 parallel_thread_integration_execute: ParallelThreadIntegrationExecute,
                 single_process_integration_execute: SingleProcessIntegrationExecute,
                 ):
        self.single_process_integration_execute = single_process_integration_execute
        self.parallel_thread_integration_execute = parallel_thread_integration_execute

    def get(
            self,
            process_count: int,
            is_async: bool = False,
    ) -> IntegrationSourceToTargetExecuteStrategy:
        if is_async:
            raise NotSupportedFeatureException(
                "async integration execute strategy is not yet wired "
                "in this build (see ADR-0032 follow-ups: asyncpg "
                "Postgres connector + async strategy registration)"
            )
        if process_count is not None and process_count > 1:
            if isinstance(self.parallel_thread_integration_execute, IntegrationSourceToTargetExecuteStrategy):
                return self.parallel_thread_integration_execute
            else:
                raise IncompatibleAdapterException(
                    f"{self.parallel_thread_integration_execute} is incompatible with {IntegrationSourceToTargetExecuteStrategy}")
        else:
            if isinstance(self.single_process_integration_execute, IntegrationSourceToTargetExecuteStrategy):
                return self.single_process_integration_execute
            else:
                raise IncompatibleAdapterException(
                    f"{self.single_process_integration_execute} is incompatible with {IntegrationSourceToTargetExecuteStrategy}")
