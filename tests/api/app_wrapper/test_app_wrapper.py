import os
from unittest import TestCase

from flask import Flask
from flask_injector import FlaskInjector
from flask_restx import Api
from injector import Injector, Binder, inject, singleton

from pdi.api.handlers.request_handler import RequestHandler
from pdi.configuration import ConfigManager
from pdi.data import DatabaseSessionManager
from pdi.data import RepositoryProvider
from pdi.utils import ModuleFinder
from pdi.api.app import FlaskAppWrapper


class DependencyWrapper:
    @inject
    def __init__(self):
        self.injector = Injector()
        self.app = Flask("test")
        self.api = Api(self.app)
        root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
        module_finder = ModuleFinder(root_directory=root_directory)
        # module_finder.import_modules(excluded_modules=['tests'])

        # Configuration initialize
        self.config_manager = ConfigManager(root_directory=root_directory, module_finder=module_finder)
        FlaskInjector(app=self.app, modules=[self.configure], injector=self.injector)

    def configure(self, binder: Binder):
        binder.bind(
            Flask,
            to=self.app
        )
        binder.bind(
            Api,
            to=self.api
        )
        for config in self.config_manager.get_all():
            binder.bind(
                config.get("type"),
                to=config.get("instance"),
                scope=singleton,
            )
        binder.bind(

            interface=DatabaseSessionManager,
            to=DatabaseSessionManager,
            scope=singleton
        )

        binder.bind(
            interface=RepositoryProvider,
            to=RepositoryProvider,
            scope=singleton
        )

        binder.bind(
            interface=FlaskAppWrapper,
            to=FlaskAppWrapper,
            scope=singleton
        )

        binder.bind(
            interface=RequestHandler,
            to=RequestHandler,
            scope=singleton
        )


class TestAppWrapper(TestCase):
    def setUp(self):
        self.dependency_wrapper = DependencyWrapper()

    def test_inject_api(self):
        @self.dependency_wrapper.app.route('/test1')
        def test_endpoint():
            return 'test'

        # database_config = dependency_wrapper.injector.get(DatabaseConfig)
        # database_session_manager = dependency_wrapper.injector.get(DatabaseSessionManager)
        # repository_provider = dependency_wrapper.injector.get(RepositoryProvider)
        # request_handler = dependency_wrapper.injector.get(RequestHandler)
        client = self.dependency_wrapper.injector.get(FlaskAppWrapper).test_client()

        response = client.get(
            'test1',
            content_type='application/json',
        )
        assert response.status_code == 200
        response_data = response.get_data(as_text=True)
        assert response_data == 'test'
