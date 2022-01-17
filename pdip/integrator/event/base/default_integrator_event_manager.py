import time

from injector import inject

from .integrator_event_manager import IntegratorEventManager
from ...operation.domain import OperationBase, OperationIntegrationBase
from ....dependency import IScoped
from ....logging.loggers.console import ConsoleLogger


class DefaultIntegratorEventManager(IScoped, IntegratorEventManager):
    @inject
    def __init__(self,
                 logger: ConsoleLogger):
        self.logger = logger

    def log(self, data: any, message: str, exception=None):
        if exception is not None:
            if isinstance(data, OperationBase):
                log_message = f'{data.Name} - {message}'
            else:
                log_message = f'{data.Order} - {data.Name} - {message}'

            self.logger.exception(exception, log_message)
        else:
            if isinstance(data, OperationBase):
                log_message = f'{data.Name} - {message}'
            else:
                log_message = f'{data.Order} - {data.Name} - {message}'
            self.logger.info(log_message)

    def initialize(self, data: OperationBase):
        message = f'{data.Name} initialized.'
        self.logger.info(message)

    def start(self, data: OperationBase):
        message = f'{data.Name} started.'
        self.logger.info(message)

    def finish(self, data: OperationBase, exception=None):
        if exception is not None:
            message = f'{data.Name} finished with error.'
            self.logger.exception(exception, message)
        else:
            message = f'{data.Name} finished.'
            self.logger.info(message)

    def integration_initialize(self, data: OperationIntegrationBase, message):
        message = f'{data.Order} - {data.Name} - {message}'
        self.logger.info(message)

    def integration_start(self, data: OperationIntegrationBase, message):
        message = f'{data.Order} - {data.Name} - {message}'
        self.logger.info(message)

    def integration_finish(self, data: OperationIntegrationBase, data_count, message, exception=None):
        if exception is not None:
            message = f'{data.Order} - {data.Name} - {message}'
            self.logger.exception(exception, message)
        else:
            message = f'{data.Order} - {data.Name} - {message}'
            self.logger.info(message)

    def integration_target_truncate(self, data: OperationIntegrationBase, row_count):
        message = f'{data.Order} - {data.Name} - Target truncate finished. (Affected Row Count:{row_count})'
        self.logger.info(message)

    def integration_execute_source(self, data: OperationIntegrationBase, row_count):
        message = f'{data.Order} - {data.Name} - Source integration completed. (Source Data Count:{row_count})'
        self.logger.info(message)

    def integration_execute_target(self, data: OperationIntegrationBase, row_count):
        message = f'{data.Order} - {data.Name} - Target integration completed. (Affected Row Count:{row_count})'
        self.logger.info(message)
        time.sleep(2)
