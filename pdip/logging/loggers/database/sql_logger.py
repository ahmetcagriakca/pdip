import traceback
from datetime import datetime
from logging import DEBUG, FATAL, ERROR, WARNING, INFO, NOTSET

from ..console.console_logger import ConsoleLogger
from ...models.log_data import LogData
from ....data.repository_provider import RepositoryProvider
from ....dependency import IScoped
from ....utils.utils import Utils
from ....configuration.models import ApplicationConfig, DatabaseConfig
from ....dependency.container import DependencyContainer
from ....exceptions.required_class_exception import RequiredClassException


class SqlLogger(IScoped):
    def __init__(self):
        pass

    @classmethod
    def log_to_db(cls, level, message, job_id=None):
        logger_class=None
        subclasses = LogData.__subclasses__()
        if subclasses is not None and len(subclasses) > 0:
            logger_class = subclasses[0]

        if logger_class is not None and DependencyContainer.Instance is not None:
            application_config: ApplicationConfig = DependencyContainer.Instance.config_manager.get(ApplicationConfig)
            database_config: DatabaseConfig = DependencyContainer.Instance.config_manager.get(DatabaseConfig)
            console_logger: ConsoleLogger = DependencyContainer.Instance.injector.get(ConsoleLogger)
            log_datetime = datetime.now()  # datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            process_info = Utils.get_process_info()
            application_name = ''
            if application_config.name is not None:
                application_name=application_config.name
            if application_config.hostname is not None:
                application_name += f'-{application_config.hostname}'
            comment = f'{application_name}-{process_info}'
            try:
                repository_provider = RepositoryProvider(database_config=database_config,database_session_manager=None)
                # repository_provider = DependencyContainer.Instance.get(RepositoryProvider)
                # repository_provider.database_session_manager.session_factory()
                log_repository = repository_provider.get(logger_class)
                log = logger_class(TypeId=level, Content=message[0:4000], LogDatetime=log_datetime,
                                   JobId=job_id, Comments=comment)
                log_repository.insert(log)
                repository_provider.commit()
            except Exception as ex:
                if job_id is not None:
                    message = f"{job_id}-{message}"
                console_logger.error(f'{message}. Sql logging getting error. Error:{ex}')
            finally:
                if job_id is not None:
                    message = f"{job_id}-{message}"
                console_logger.log(level, f'{message}')
        else:
            if job_id is not None:
                message = f"{job_id}-{message}"
            ConsoleLogger().log(level, f'{message}')

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
