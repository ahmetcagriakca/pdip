import traceback
from datetime import datetime
from logging import DEBUG, FATAL, ERROR, WARNING, INFO, NOTSET

from injector import inject

from ..console import ConsoleLogger
from ...models import LogData
from ....configuration.models.application import ApplicationConfig
from ....configuration.models.database import DatabaseConfig
from ....data import RepositoryProvider
from ....dependency import IScoped
from ....utils.utils import Utils


class SqlLogger(IScoped):
    @inject
    def __init__(self,
                 application_config: ApplicationConfig,
                 database_config: DatabaseConfig,
                 console_logger: ConsoleLogger):
        self.console_logger = console_logger
        self.database_config = database_config
        self.application_config = application_config

    def log_to_db(self, level, message, job_id=None):
        logger_class = None
        subclasses = LogData.__subclasses__()
        if subclasses is not None and len(subclasses) > 0:
            logger_class = subclasses[0]

        if logger_class is not None:
            log_datetime = datetime.now()  # datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            process_info = Utils.get_process_info()
            application_name = ''
            if self.application_config.name is not None:
                application_name = self.application_config.name
            if self.application_config.hostname is not None:
                application_name += f'-{self.application_config.hostname}'
            comment = f'{application_name}-{process_info}'
            try:
                repository_provider = RepositoryProvider(database_config=self.database_config,
                                                         database_session_manager=None)
                log_repository = repository_provider.get(logger_class)
                log = logger_class(TypeId=level, Content=message[0:4000], LogDatetime=log_datetime,
                                   JobId=job_id, Comments=comment)
                log_repository.insert(log)
                repository_provider.commit()
            except Exception as ex:
                if job_id is not None:
                    message = f"{job_id}-{message}"
                self.console_logger.error(f'{message}. Sql logging getting error. Error:{ex}')
            finally:
                if job_id is not None:
                    message = f"{job_id}-{message}"
                self.console_logger.log(level, f'{message}')
        else:
            if job_id is not None:
                message = f"{job_id}-{message}"
            self.console_logger.log(level, f'{message}')

    #######################################################################################
    def logger_method(self, level, message, job_id=None):
        self.log_to_db(level=level, message=message, job_id=job_id)

    #######################################################################################
    def exception(self, exception: Exception, message: str = None, job_id=None):
        exc = traceback.format_exc() + '\n' + str(exception)
        message += f"Error: {exc}"
        self.logger_method(ERROR, message, job_id)

    #######################################################################################
    def fatal(self, message, job_id=None):
        self.logger_method(FATAL, message, job_id)

    #######################################################################################
    def error(self, message, job_id=None):
        self.logger_method(ERROR, message, job_id)

    #######################################################################################
    def warning(self, message, job_id=None):
        self.logger_method(WARNING, message, job_id)

    #######################################################################################
    def info(self, message, job_id=None):
        self.logger_method(INFO, message, job_id)

    #######################################################################################
    def debug(self, message, job_id=None):
        self.logger_method(DEBUG, message, job_id)

    #######################################################################################
    def log(self, message, job_id=None):
        self.logger_method(NOTSET, message, job_id)
