from injector import inject
from sqlalchemy.exc import OperationalError

from .seed import Seed
from ..base import DatabaseSessionManager
from ...dependency import IScoped
from ...dependency.provider import ServiceProvider
from ...logging.loggers.sql import SqlLogger


class SeedRunner(IScoped):
    @inject
    def __init__(self,
                 logger: SqlLogger,
                 service_provider: ServiceProvider,
                 ):
        self.service_provider = service_provider
        self.logger = logger

    def run(self):
        try:
            # trying to connect database first
            database_session_manager = self.service_provider.get(DatabaseSessionManager)
            database_session_manager.connect()
            for seed_class in Seed.__subclasses__():
                try:
                    instance = self.service_provider.get(seed_class)
                    instance.seed()
                except Exception as ex:
                    self.logger.exception(ex, "Class instance not found on container.")
                    instance = seed_class()
                    instance.seed()

        except OperationalError as opex:
            self.logger.exception(opex, "Database connection getting error on running seeds.")
        except Exception as ex:
            self.logger.exception(ex, "Seeds getting error.")
        finally:
            self.service_provider.get(DatabaseSessionManager).close()
