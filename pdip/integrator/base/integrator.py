from .integrator_event_manager import DefaultIntegratorEventManager
from ..domain.enums.events import EVENT_EXECUTION_INITIALIZED, EVENT_EXECUTION_FINISHED, \
    EVENT_EXECUTION_STARTED, EVENT_EXECUTION_INTEGRATION_INITIALIZED, EVENT_EXECUTION_INTEGRATION_STARTED, \
    EVENT_EXECUTION_INTEGRATION_FINISHED, EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE, \
    EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET, EVENT_LOG, EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE
from ..operation.base import OperationExecution
from ..operation.domain import OperationBase
from ..operation.domain.operation import OperationExecutionBase, \
    OperationIntegrationExecutionBase
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
        self.message_broker: MessageBroker = None

    def __del__(self):
        self.close()

    def initialize(self):
        self.message_broker = MessageBroker(self.logger)
        self.register_default_event_listeners(self.integrator_event_manager)
        self.message_broker.start()

    def close(self):
        if hasattr(self, 'message_broker'):
            del self.message_broker

    def integrate(self, operation: any):
        if operation is None:
            raise Exception('Operation required')
        self.initialize()

        if isinstance(operation, OperationBase):
            self.initialize_events(execution_id=None, operation=operation)
            self.operation_execution.start(operation, self.message_broker.get_publish_channel())
        elif isinstance(operation, str) or isinstance(operation, dict):
            self.operation_execution.start(operation, self.message_broker.get_publish_channel())
        self.message_broker.join()
        self.close()

    def initialize_events(self, execution_id: int, operation: OperationBase):
        operation_execution = OperationExecutionBase(
            Id=execution_id,
            OperationId=operation.Id,
            Name=operation.Name,
            Events=[]
        )
        operation.Execution = operation_execution

        for operation_integration in operation.Integrations:
            operation_integration_execution = OperationIntegrationExecutionBase(
                Id=None,
                OperationIntegrationId=operation_integration.Id,
                Name=operation_integration.Name,
                Events=[]
            )
            operation_integration.Execution = operation_integration_execution

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
