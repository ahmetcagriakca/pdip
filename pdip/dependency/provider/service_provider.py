import os

from multiprocessing.process import current_process
from typing import List, TypeVar, Type

from flask import Flask
from flask_injector import FlaskInjector, request
from flask_restx import Api
from injector import singleton, Injector, threadlocal, Binder
from werkzeug.utils import redirect

from pdip import Utils
from pdip.dependency.scopes import ISingleton, IScoped
from pdip.api.base import ResourceBase
from pdip.configuration.models import ApiConfig, ApplicationConfig, DatabaseConfig
from pdip.configuration import ConfigManager
from pdip.logging.loggers.console.console_logger import ConsoleLogger
from pdip.utils import ModuleFinder

T = TypeVar('T')


class ServiceProvider:

    def __init__(self, root_directory: str, excluded_modules: [] = None):
        self.root_directory = root_directory
        self.excluded_modules = excluded_modules
        self.app: Flask = None
        self.api: Api = None
        self.config_manager: ConfigManager = None
        self.module_finder: ModuleFinder = None
        self.injector: Injector = None
        self.binder: Injector = None
        self.logger = ConsoleLogger()
        # print(f'root:{root_directory}')
        self.logger.info(f"Application initialize started")
        self.configure_startup(self.root_directory)
        self.process_info()

    def __del__(self):
        del self.api
        del self.app
        self.module_finder.cleanup()

    def get(self, instance_type: Type[T]) -> T:
        return self.injector.get(instance_type)

    def configure_startup(self, root_directory):
        # Importing all modules for dependency
        self.module_finder = ModuleFinder(root_directory=root_directory)
        self.config_manager = ConfigManager(
            root_directory=root_directory, module_finder=self.module_finder)
        excluded_modules = ['controllers']
        if self.excluded_modules is not None:
            excluded_modules += self.excluded_modules
        self.module_finder.import_modules(excluded_modules=excluded_modules)

        # Configuration initialize
        if self.config_manager.get(ApplicationConfig) is None:
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
            self.config_manager.set(
                DatabaseConfig, "connection_string", Utils.get_connection_string(
                    database_config=database_config, root_directory=self.root_directory))

    def configure(self, binder: Binder):
        self.binder = binder
        self.binder.bind(
            interface=ModuleFinder,
            to=self.module_finder
        )

        if self.app is not None:
            self.binder.bind(
                interface=Flask,
                to=self.app
            )
        if self.api is not None:
            self.binder.bind(
                interface=Api,
                to=self.api
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
        for controller in ResourceBase.__subclasses__():
            self.binder.bind(
                interface=controller,
                to=controller,
                scope=request,
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

    def initialize_injection(self):
        self.injector = Injector(self.configure)

    def initialize_api_injection(self):
        self.injector = Injector()
        self.import_controllers()
        FlaskInjector(app=self.app, modules=[
            self.configure], injector=self.injector)

    def import_controllers(self):
        self.module_finder.import_modules(included_modules=['controllers'])

    def is_flask_api(self):
        api_config: ApiConfig = self.config_manager.get(ApiConfig)
        return api_config is not None

    def initialize_flask(self):
        application_config: ApplicationConfig = self.config_manager.get(
            ApplicationConfig)
        api_config: ApiConfig = self.config_manager.get(ApiConfig)
        application_name = ''
        if application_config is not None and application_config.name is not None:
            application_name = application_config.name
        if api_config is not None:
            self.app = Flask(application_name)
            base_url = '/'
            if api_config.base_url is not None:
                base_url = api_config.base_url
            doc_url = '/documentation'
            if api_config.doc_url is not None:
                doc_url = api_config.doc_url

            @self.app.route(base_url)
            def home_redirect():
                return redirect(doc_url, code=302, Response=None)

            self.api = Api(self.app,
                           title=f'{application_name} API',
                           version=api_config.version,
                           doc=doc_url,
                           base_url=base_url)
