from injector import inject

from ..initializer.integrator import IntegratorInitializerFactory
from ..operation.base import OperationExecution
from ..operation.domain import OperationBase
from ..pubsub.base import MessageBroker
from ...logging.loggers.console import ConsoleLogger
from ...observability import get_tracer


class Integrator:
    @inject
    def __init__(
            self,
            logger: ConsoleLogger,
            integrator_initializer_factory: IntegratorInitializerFactory,
            operation_execution: OperationExecution
    ):
        self.operation_execution = operation_execution
        self.logger = logger
        self.integrator_initializer_factory = integrator_initializer_factory
        self.message_broker = MessageBroker(self.logger)

    def __del__(self):
        self.close()

    def close(self):
        if hasattr(self, 'message_broker'):
            del self.message_broker

    def integrate(
            self,
            operation: any,
            execution_id: int = None,
            ap_scheduler_job_id: int = None
    ):
        if operation is None:
            raise Exception('Operation required')

        if isinstance(operation, OperationBase):
            with get_tracer("pdip.integrator").start_as_current_span(
                    "pdip.integrator.job"
            ) as span:
                span.set_attribute(
                    "pdip.integration.id",
                    operation.Id if operation.Id is not None else 0,
                )
                span.set_attribute(
                    "pdip.integration.name", operation.Name or ""
                )
                try:
                    operation = self.integrator_initializer_factory \
                        .get() \
                        .initialize(operation=operation,
                                    message_broker=self.message_broker,
                                    execution_id=execution_id,
                                    ap_scheduler_job_id=ap_scheduler_job_id
                                    )
                    self.operation_execution.start(
                        operation=operation,
                        channel=self.message_broker.get_publish_channel()
                    )
                except Exception as ex:
                    raise
                finally:
                    self.message_broker.join()
                    self.close()
        else:
            raise Exception('Operation type is not suitable')

    def subscribe(self, event, callback):
        self.message_broker.subscribe(event, callback)

    def unsubscribe(self, event, callback):
        self.message_broker.unsubscribe(event, callback)
