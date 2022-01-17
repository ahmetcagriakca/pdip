from abc import abstractmethod

from ..base import Initializer
from ...operation.domain import OperationBase


class ExecutionInitializer(Initializer):

    @abstractmethod
    def initialize(
            self,
            operation: OperationBase,
            execution_id: int = None,
            ap_scheduler_job_id: int = None
    ) -> OperationBase:
        pass
