from injector import inject

from .integrator_initializer import IntegratorInitializer
from ..execution.base import ExecutionInitializerFactory
from ...domain.enums.events import EVENT_EXECUTION_INITIALIZED, EVENT_EXECUTION_FINISHED, \
    EVENT_EXECUTION_STARTED, EVENT_EXECUTION_INTEGRATION_INITIALIZED, EVENT_EXECUTION_INTEGRATION_STARTED, \
    EVENT_EXECUTION_INTEGRATION_FINISHED, EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE, \
    EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET, EVENT_LOG, EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE
from ...event.base import IntegratorEventManagerFactory
from ...operation.domain import OperationBase
from ...pubsub.base import MessageBroker
from ....dependency import IScoped


class DefaultIntegratorInitializer(IntegratorInitializer, IScoped):
    @inject
    def __init__(
            self,
            integrator_event_manager_factory: IntegratorEventManagerFactory = None,
            execution_initializer_factory: ExecutionInitializerFactory = None,
    ):
        self.execution_initializer_factory = execution_initializer_factory
        self.integrator_event_manager_factory = integrator_event_manager_factory

    def initialize(
            self,
            operation: OperationBase,
            message_broker: MessageBroker,
            execution_id: int = None,
            ap_scheduler_job_id: int = None
    ) -> OperationBase:
        message_broker.initialize()
        self.register_default_event_listeners(message_broker)
        message_broker.start()
        operation = self.execution_initializer_factory \
            .get() \
            .initialize(operation=operation,
                        execution_id=execution_id,
                        ap_scheduler_job_id=ap_scheduler_job_id
                        )
        return operation

    def register_default_event_listeners(
            self,
            message_broker: MessageBroker
    ):
        integrator_event_manager = self.integrator_event_manager_factory.get()
        message_broker.subscribe(EVENT_LOG, integrator_event_manager.log)
        message_broker.subscribe(EVENT_EXECUTION_INITIALIZED, integrator_event_manager.initialize)
        message_broker.subscribe(EVENT_EXECUTION_STARTED, integrator_event_manager.start)
        message_broker.subscribe(EVENT_EXECUTION_FINISHED, integrator_event_manager.finish)
        message_broker.subscribe(EVENT_EXECUTION_INTEGRATION_INITIALIZED,
                                 integrator_event_manager.integration_initialize)
        message_broker.subscribe(EVENT_EXECUTION_INTEGRATION_STARTED, integrator_event_manager.integration_start)
        message_broker.subscribe(EVENT_EXECUTION_INTEGRATION_FINISHED, integrator_event_manager.integration_finish)
        message_broker.subscribe(EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE,
                                 integrator_event_manager.integration_target_truncate)
        message_broker.subscribe(EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE,
                                 integrator_event_manager.integration_execute_source)
        message_broker.subscribe(EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET,
                                 integrator_event_manager.integration_execute_target)
