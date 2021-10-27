import os
from multiprocessing.process import current_process
from typing import TypeVar, Type

from injector import singleton, Injector, threadlocal, Binder

from ...configuration import ConfigManager
from ...configuration.models.api import ApiConfig
from ...configuration.models.application import ApplicationConfig
from ...configuration.models.database import DatabaseConfig
from ...dependency import ISingleton, IScoped
from ...dependency.provider.api_provider import ApiProvider
from ...logging.loggers.console.console_logger import ConsoleLogger
from ...utils import ModuleFinder
from ...utils import Utils

T = TypeVar('T')


class ServiceProvider:
    """
    """

    def __init__(self,
                 root_directory: str = None,
                 configurations: [] = None,
                 excluded_modules: [] = None):
        self.root_directory = root_directory
        self.excluded_modules = excluded_modules
        self.api_provider: ApiProvider = None
        self.injector = Injector()
        self.config_manager: ConfigManager = None
        self.module_finder: ModuleFinder = None
        self.binder: Injector = None
        self.logger = ConsoleLogger()
        self.logger.info(f"Application initialize started")
        if configurations is not None:
            self.modules = [self.configure] + configurations
        else:
            self.modules = [self.configure]

        self.configure_startup(self.root_directory)
        self.process_info()

    def __del__(self):
        if hasattr(self, 'api_provider') and self.api_provider is not None:
            del self.api_provider
        self.module_finder.cleanup()

    def get(self, instance_type: Type[T]) -> T:
        return self.injector.get(instance_type)

    def configure_startup(self, root_directory):
        # Importing all modules for dependency
        self.module_finder = ModuleFinder(root_directory=root_directory)
        # excluded_modules = ['controllers']
        excluded_modules = []
        if self.excluded_modules is not None:
            excluded_modules += self.excluded_modules
        self.module_finder.import_modules(excluded_modules=excluded_modules)

        self.config_manager = ConfigManager(
            root_directory=root_directory, module_finder=self.module_finder)

        # Configuration initialize
        application_config = self.config_manager.get(ApplicationConfig)
        if application_config is None or application_config.root_directory is None or application_config.root_directory == '':
            self.config_manager.set(
                ApplicationConfig, "root_directory", self.root_directory)
        self.set_config_values_name()

    def set_config_values_name(self):
        application_config = self.config_manager.get(ApplicationConfig)
        database_config: DatabaseConfig = self.config_manager.get(
            DatabaseConfig)
        if database_config is not None and database_config.application_name is None:
            process_info = self.get_process_info()
            hostname = os.getenv('HOSTNAME', '')
            self.config_manager.set(ApplicationConfig, "hostname", hostname)
            self.config_manager.set(
                DatabaseConfig, "application_name", f"{application_config.name}-({process_info})")
            if database_config.connection_string is None or database_config.connection_string == '':
                self.config_manager.set(DatabaseConfig, "connection_string", Utils.get_connection_string(
                    database_config=database_config, root_directory=self.root_directory))

    def configure(self, binder: Binder):
        self.binder = binder
        self.binder.bind(
            interface=ServiceProvider,
            to=self
        )
        self.binder.bind(
            interface=ModuleFinder,
            to=self.module_finder
        )
        self.binder.bind(
            interface=ConfigManager,
            to=self.config_manager
        )

        for config in self.config_manager.get_all():
            self.binder.bind(
                interface=config.get("type"),
                to=config.get("instance"),
                scope=singleton,
            )

        for singletonScope in ISingleton.__subclasses__():
            self.binder.bind(
                interface=singletonScope,
                to=singletonScope,
                scope=singleton,
            )

        for scoped in IScoped.__subclasses__():
            self.binder.bind(
                interface=scoped,
                to=scoped,
                scope=threadlocal,
            )

    def get_process_info(self):
        return f"{current_process().name} ({os.getpid()},{os.getppid()})"

    def process_info(self):
        logger = ConsoleLogger()
        application_config: ApplicationConfig = self.config_manager.get(
            ApplicationConfig)
        if application_config is not None:
            hostname = f'-{application_config.hostname}' if (
                    application_config.hostname is not None and application_config.hostname != '') else ''
            logger.info(f"Application : {application_config.name}{hostname}")

    def initialize_injection(self, initialize_flask):
        if self.is_flask_api() and initialize_flask:

            application_config: ApplicationConfig = self.config_manager.get(
                ApplicationConfig)
            api_config: ApiConfig = self.config_manager.get(ApiConfig)
            self.api_provider = ApiProvider(modules=self.modules, application_config=application_config,
                                            api_config=api_config, injector=self.injector)
            self.api_provider.initialize()
        else:
            for module in self.modules:
                self.injector.binder.install(module)

    def is_flask_api(self):
        api_config: ApiConfig = self.config_manager.get(ApiConfig)
        return api_config is not None and api_config.is_debug is not None
