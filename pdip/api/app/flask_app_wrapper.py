import sys

from flask import Flask
from flask_restx import Api
from injector import inject
from werkzeug.exceptions import HTTPException
from flask_cors import CORS

from pdip.api.base.resource_base import ResourceBase

from ..handlers.error_handlers import ErrorHandlers
from ..handlers.request_handler import RequestHandler
from ...configuration.models.api import ApiConfig
from ...configuration.models.application import ApplicationConfig

from ...dependency.scopes import ISingleton
from ...exceptions.operational_exception import OperationalException


class FlaskAppWrapper(ISingleton):
    @inject
    def __init__(self,
                 request_handler: RequestHandler,
                 app: Flask,
                 api: Api,
                 api_config: ApiConfig,
                 error_handlers: ErrorHandlers,
                 application_config: ApplicationConfig,
                 ):
        self.application_config = application_config
        self.api = api
        self.request_handler = request_handler
        self.app = app
        self.api_config = api_config
        self.error_handlers = error_handlers
        # Application create operations
        self.create_application()
        # self.find_resources()

    # Application flask configurations and api endpoint registration
    def create_application(self):
        CORS(self.app, resources={r"/api/*": {"origins": "*"}})
        self.register_error_handlers()

    def register_error_handlers(self):
        self.api.errorhandler(OperationalException)(self.error_handlers.handle_operational_exception)
        self.app.register_error_handler(Exception, self.error_handlers.handle_exception)
        self.app.register_error_handler(HTTPException, self.error_handlers.handle_http_exception)
        self.app.after_request(self.request_handler.after_request)

    # def find_resources(self):
    #     for resource in ResourceBase.__subclasses__():
    #         if sys.modules[resource.__module__].__file__.startswith(self.application_config.root_directory):
    #             con = Controller(
    #                 cls=resource, api=self.api, application_config=self.application_config, namespace=None, route=None)
    #             con.create_route()

    def run(self):
        self.app.run(debug=self.api_config.is_debug, host='0.0.0.0', port=self.api_config.port)

    def test_client(self):
        return self.app.test_client()
