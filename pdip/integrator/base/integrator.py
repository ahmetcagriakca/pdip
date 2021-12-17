from .integrator_events import IntegratorEvents
from ..models.enums.events import EVENT_EXECUTION_INITIALIZED, EVENT_EXECUTION_FINISHED, \
    EVENT_EXECUTION_STARTED, EVENT_EXECUTION_INTEGRATION_INITIALIZED, EVENT_EXECUTION_INTEGRATION_STARTED, \
    EVENT_EXECUTION_INTEGRATION_FINISHED, EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE, \
    EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET, EVENT_LOG, EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE
from ..operation.base import OperationExecution
from ..operation.domain import OperationBase
from ..pubsub.event_channel import EventChannel
from ...dependency.container import DependencyContainer
from ...logging.loggers.console import ConsoleLogger


class Integrator:
    def __init__(self):
        self.handlers = []
        self.logger = DependencyContainer.Instance.get(ConsoleLogger)
        self.event_channel = EventChannel(self.logger)
        self.operation_execution = DependencyContainer.Instance.get(OperationExecution)
        self.integrator_events = DependencyContainer.Instance.get(IntegratorEvents)
        self.register_default_event_listeners()

    def integrate(self, operation: any):
        if isinstance(operation, OperationBase):
            self.operation_execution.start(operation, self.event_channel)
        elif isinstance(operation, str) or isinstance(operation, dict):
            self.operation_execution.start(operation)

    def subscribe(self, event, callback):
        self.event_channel.subscribe(event, callback)

    def unsubscribe(self, event, callback):
        self.event_channel.unsubscribe(event, callback)

    def register_default_event_listeners(self):
        self.subscribe(EVENT_LOG, self.integrator_events.log)
        self.subscribe(EVENT_EXECUTION_INITIALIZED, self.integrator_events.initialize)
        self.subscribe(EVENT_EXECUTION_STARTED, self.integrator_events.start)
        self.subscribe(EVENT_EXECUTION_FINISHED, self.integrator_events.finish)
        self.subscribe(EVENT_EXECUTION_INTEGRATION_INITIALIZED, self.integrator_events.integration_initialize)
        self.subscribe(EVENT_EXECUTION_INTEGRATION_STARTED, self.integrator_events.integration_start)
        self.subscribe(EVENT_EXECUTION_INTEGRATION_FINISHED, self.integrator_events.integration_finish)
        self.subscribe(EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE,
                       self.integrator_events.integration_target_truncate)
        self.subscribe(EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE,
                       self.integrator_events.integration_execute_source)
        self.subscribe(EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET,
                       self.integrator_events.integration_execute_target)
