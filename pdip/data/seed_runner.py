from injector import inject
from sqlalchemy.exc import OperationalError

from .database_session_manager import DatabaseSessionManager
from .seed import Seed
from ..dependency import IScoped
from ..dependency.container import DependencyContainer
from ..logging.loggers.database import SqlLogger


class SeedRunner(IScoped):
    @inject
    def __init__(self,
                 database_session_manager: DatabaseSessionManager,
                 logger: SqlLogger

                 ):
        self.logger = logger
        self.database_session_manager = database_session_manager

    def run(self):
        try:
            self.database_session_manager.engine.connect()
            for seedClass in Seed.__subclasses__():
                try:
                    instance = DependencyContainer.Instance.get(seedClass)
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
            self.database_session_manager.close()
