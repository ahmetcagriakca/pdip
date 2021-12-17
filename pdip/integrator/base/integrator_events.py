from injector import inject

from pdip.dependency import IScoped
from pdip.integrator.operation.domain import OperationBase, OperationIntegrationBase
from pdip.logging.loggers.console import ConsoleLogger


class IntegratorEvents(IScoped):
    @inject
    def __init__(self,
                 logger: ConsoleLogger):
        self.logger = logger

    def log(self, data: any, log: str, exception=None):
        if exception is not None:
            if isinstance(data, OperationBase):
                message = f'{data.Name} - {log}'
            else:
                message = f'{data.Order} - {data.Integration.Name} - {log}'

            self.logger.exception(exception, message)
        else:
            if isinstance(data, OperationBase):
                message = f'{data.Name} - {log}'
            else:
                message = f'{data.Order} - {data.Integration.Name} - {log}'
            self.logger.info(message)

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
        message = f'{data.Order} - {data.Integration.Name} - {message}'
        self.logger.info(message)

    def integration_start(self, data: OperationIntegrationBase, message):
        message = f'{data.Order} - {data.Integration.Name} - {message}'
        self.logger.info(message)

    def integration_finish(self, data: OperationIntegrationBase, data_count, message, exception=None):
        if exception is not None:
            message = f'{data.Order} - {data.Integration.Name} - {message}'
            self.logger.exception(exception, message)
        else:
            message = f'{data.Order} - {data.Integration.Name} - {message}'
            self.logger.info(message)

    def integration_target_truncate(self, data: OperationIntegrationBase, row_count):
        message = f'{data.Order} - {data.Integration.Name} - Target truncate finished. (Affected Row Count:{row_count})'
        self.logger.info(message)

    def integration_execute_source(self, data: OperationIntegrationBase, row_count):
        message = f'{data.Order} - {data.Integration.Name} - Source integration completed. (Source Data Count:{row_count})'
        self.logger.info(message)

    def integration_execute_target(self, data: OperationIntegrationBase, row_count):
        message = f'{data.Order} - {data.Integration.Name} - Target integration completed. (Affected Row Count:{row_count})'
        self.logger.info(message)
