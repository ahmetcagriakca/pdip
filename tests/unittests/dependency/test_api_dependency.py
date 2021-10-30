import sys
from unittest import TestCase

from flask import Flask
from flask_injector import FlaskInjector
from flask_restx import Api
from injector import Injector, Binder, inject, singleton


class AppWrapper:
    @inject
    def __init__(self,
                 app: Flask,
                 api: Api
                 ):
        self.api = api
        self.app = app

    def run(self):
        self.app.run(host='0.0.0.0')

    def test_client(self):
        return self.app.test_client()


class DependencyWrapper:
    @inject
    def __init__(self):
        self.injector = Injector()
        self.app = Flask("test")
        self.api = Api(self.app)
        FlaskInjector(app=self.app, modules=[
            self.configure], injector=self.injector)

    def configure(self, binder: Binder):
        binder.bind(
            Flask,
            to=self.app
        )
        binder.bind(
            Api,
            to=self.api
        )

        binder.bind(
            AppWrapper,
            to=AppWrapper,
            scope=singleton
        )


class TestApiDependency(TestCase):
    def tearDown(self):
        return super().tearDown()

    def test_inject_api(self):
        dependency_wrapper = DependencyWrapper()

        @dependency_wrapper.app.route('/test')
        def test_endpoint():
            return 'test'

        client = dependency_wrapper.injector.get(AppWrapper).test_client()

        response = client.get(
            'test',
            content_type='application/json',
        )
        assert response.status_code == 200
        response_data = response.get_data(as_text=True)
        assert response_data == 'test'
