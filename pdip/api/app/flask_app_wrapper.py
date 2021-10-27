from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from injector import inject
from werkzeug.exceptions import HTTPException

from ..handlers import ErrorHandlers
from ..handlers import RequestHandler
from ...configuration.models.api import ApiConfig
from ...configuration.models.application import ApplicationConfig
from ...dependency import ISingleton
from ...exceptions import OperationalException


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

    def run(self):
        self.app.run(debug=self.api_config.is_debug, host='0.0.0.0', port=self.api_config.port)

    def test_client(self):
        return self.app.test_client()
