import sys

from typing import TypeVar

from flask import Flask
from flask_injector import FlaskInjector, request
from flask_restx import Api
from injector import Injector, Binder
from werkzeug.utils import redirect

from pdip.api.base.controller_base import Controller
from pdip.api.base import ResourceBase
from pdip.configuration.models import ApiConfig, ApplicationConfig
from pdip.logging.loggers.console.console_logger import ConsoleLogger

T = TypeVar('T')


class ApiProvider:
    def __init__(self,
                 modules: [] = None,
                 application_config: ApplicationConfig = None,
                 api_config: ApiConfig = None,
                 injector: Injector = None):
        self.modules = modules
        self.injector = injector
        self.api_config = api_config
        self.application_config = application_config
        self.app: Flask = None
        self.api: Api = None
        self.binder: Binder = None
        self.logger = ConsoleLogger()

    def __del__(self):
        del self.api
        del self.app

    def initialize(self):
        self.initialize_flask()
        FlaskInjector(app=self.app, modules=[self.api_configure] + self.modules, injector=self.injector)

    def api_configure(self, binder: Binder):
        self.binder = binder

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
        for controller in ResourceBase.__subclasses__():
            self.binder.bind(
                interface=controller,
                to=controller,
                scope=request,
            )

    def initialize_flask(self):
        application_name = ''
        if self.application_config is not None and self.application_config.name is not None:
            application_name = self.application_config.name
        if self.api_config is not None:
            self.app = Flask(application_name)
            base_url = '/'
            if self.api_config.base_url is not None:
                base_url = self.api_config.base_url
            doc_url = '/documentation'
            if self.api_config.doc_url is not None:
                doc_url = self.api_config.doc_url

            @self.app.route(base_url)
            def home_redirect():
                return redirect(doc_url, code=302, Response=None)

            self.api = Api(self.app,
                           title=f'{application_name}',
                           version=self.api_config.version,
                           doc=doc_url,
                           base_url=base_url)
        self.find_resources()

    def find_resources(self):
        for resource in ResourceBase.__subclasses__():
            if resource.__module__ in sys.modules and sys.modules[resource.__module__].__file__.startswith(self.application_config.root_directory):
                namespace = None
                route = None
                if hasattr(resource, 'namespace'):
                    namespace = resource.namespace
                if hasattr(resource, 'route'):
                    route = resource.route
                con = Controller(
                    cls=resource,
                    api=self.api,
                    application_config=self.application_config,
                    namespace=namespace,
                    route=route)
                con.create_route()
