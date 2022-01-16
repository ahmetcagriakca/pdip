from . import DefaultIntegratorEventManager
from ..domain.enums.events import EVENT_EXECUTION_INITIALIZED, EVENT_EXECUTION_FINISHED, \
    EVENT_EXECUTION_STARTED, EVENT_EXECUTION_INTEGRATION_INITIALIZED, EVENT_EXECUTION_INTEGRATION_STARTED, \
    EVENT_EXECUTION_INTEGRATION_FINISHED, EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE, \
    EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET, EVENT_LOG, EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE
from ..operation.base import OperationExecution
from ..operation.domain import OperationBase
from ..operation.domain.operation import ExecutionOperationBase, \
    ExecutionOperationIntegrationBase
from ..pubsub.base import MessageBroker
from ...dependency.container import DependencyContainer
from ...logging.loggers.console import ConsoleLogger


class Integrator:
    def __init__(self, logger=None, integrator_event_manager=None):
        self.operation_execution = DependencyContainer.Instance.get(OperationExecution)
        if integrator_event_manager is None:
            self.integrator_event_manager = DependencyContainer.Instance.get(DefaultIntegratorEventManager)
        else:
            self.integrator_event_manager = integrator_event_manager
        if logger is None:
            self.logger = DependencyContainer.Instance.get(ConsoleLogger)
        else:
            self.integrator_event_manager = logger
        self.message_broker = MessageBroker(self.logger)

    def __del__(self):
        self.close()

    def close(self):
        if hasattr(self, 'message_broker'):
            del self.message_broker

    def __initialize(self):
        self.message_broker.initialize()
        self.register_default_event_listeners(self.integrator_event_manager)
        self.message_broker.start()

    def integrate(self, operation: any, execution_id: int = None, ap_scheduler_job_id: int = None):
        if operation is None:
            raise Exception('Operation required')

        if isinstance(operation, OperationBase):
            self.__initialize()
            operation = self.initialize_execution(operation=operation, execution_id=execution_id,
                                                  ap_scheduler_job_id=ap_scheduler_job_id)
            self.operation_execution.start(operation, self.message_broker.get_publish_channel())
            self.message_broker.join()
            self.close()
        else:
            raise Exception('Operation type is not suitable')

    def initialize_execution(self, operation: OperationBase, execution_id: int = None, ap_scheduler_job_id: int = None):
        execution_operation = ExecutionOperationBase(
            Id=execution_id,
            ApSchedulerJobId=ap_scheduler_job_id,
            OperationId=operation.Id,
            Name=operation.Name,
            Events=[]
        )
        operation.Execution = execution_operation

        for operation_integration in operation.Integrations:
            execution_operation_integration = ExecutionOperationIntegrationBase(
                Id=None,
                OperationId=operation.Id,
                OperationExecutionId=execution_id,
                ApSchedulerJobId=ap_scheduler_job_id,
                OperationIntegrationId=operation_integration.Id,
                Name=operation_integration.Name,
                Events=[]
            )
            operation_integration.Execution = execution_operation_integration
        return operation

    def subscribe(self, event, callback):
        self.message_broker.subscribe(event, callback)

    def unsubscribe(self, event, callback):
        self.message_broker.unsubscribe(event, callback)

    def register_default_event_listeners(self, integrator_event_manager):
        self.subscribe(EVENT_LOG, integrator_event_manager.log)
        self.subscribe(EVENT_EXECUTION_INITIALIZED, integrator_event_manager.initialize)
        self.subscribe(EVENT_EXECUTION_STARTED, integrator_event_manager.start)
        self.subscribe(EVENT_EXECUTION_FINISHED, integrator_event_manager.finish)
        self.subscribe(EVENT_EXECUTION_INTEGRATION_INITIALIZED, integrator_event_manager.integration_initialize)
        self.subscribe(EVENT_EXECUTION_INTEGRATION_STARTED, integrator_event_manager.integration_start)
        self.subscribe(EVENT_EXECUTION_INTEGRATION_FINISHED, integrator_event_manager.integration_finish)
        self.subscribe(EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE,
                       integrator_event_manager.integration_target_truncate)
        self.subscribe(EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE,
                       integrator_event_manager.integration_execute_source)
        self.subscribe(EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET,
                       integrator_event_manager.integration_execute_target)
