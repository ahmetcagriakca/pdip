from injector import inject

from pdip.dependency import IScoped
from pdip.logging.loggers.console import ConsoleLogger
from pdip.processing import ProcessManager


class ProcessManagerFactory(IScoped):
    @inject
    def __init__(self, logger: ConsoleLogger):
        self.logger = logger

    def get(self):
        process_manager = ProcessManager(logger=self.logger)
        return process_manager
