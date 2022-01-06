from injector import inject
from sqlalchemy.exc import OperationalError

from .seed import Seed
from ..repository import RepositoryProvider
from ...dependency import IScoped
from ...dependency.provider import ServiceProvider
from ...logging.loggers.sql import SqlLogger


class SeedRunner(IScoped):
    @inject
    def __init__(self,
                 logger: SqlLogger,
                 repository_provider: RepositoryProvider,
                 service_provider: ServiceProvider,
                 ):
        self.service_provider = service_provider
        self.repository_provider = repository_provider
        self.logger = logger

    def run(self):
        try:
            for seedClass in Seed.__subclasses__():
                try:
                    instance = self.service_provider.get(seedClass)
                    instance.seed()
                except Exception as ex:
                    self.logger.exception(ex, "Class instance not found on container.")
                    instance = seedClass()
                    instance.seed()

        except OperationalError as opex:
            self.logger.exception(opex, "Database connection getting error on running seeds.")
        except Exception as ex:
            self.logger.exception(ex, "Seeds getting error.")
        finally:
            self.repository_provider.close()
