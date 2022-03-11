from injector import inject

from ..base import ParallelSessionBroker
from .........dependency import IScoped
from .........logging.loggers.console import ConsoleLogger


class ParallelSessionBrokerFactory(IScoped):
    @inject
    def __init__(self, logger: ConsoleLogger):
        self.logger = logger

    def get(self):
        process_manager = ParallelSessionBroker(logger=self.logger)
        return process_manager
