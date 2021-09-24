import os
import sys

from flask_restx import Api

from .endpoint_base import endpoint
from ...dependency.container import DependencyContainer
from ...utils.utils import Utils
from ...configuration.models.application_config import ApplicationConfig


class Controller:
    def __init__(self,
                 cls,
                 api,
                 application_config: ApplicationConfig,
                 namespace=None,
                 route=None
                 ):
        self.route = route
        self.cls = cls
        self.namespace = namespace
        self.application_config = application_config
        self.api = api
        self.white_list = ['get', 'post', 'put', 'delete']

    def create_route(self):

        controller_namespace = self.namespace
        if controller_namespace is None:
            controller_namespace = self.find_namespace()

        controller_route = self.route
        if controller_route is None:
            controller_route = self.find_route()

        decorator = endpoint(namespace=controller_namespace)
        for attr in self.cls.__dict__:
            if callable(getattr(self.cls, attr)) and attr in self.white_list:
                setattr(self.cls, attr, decorator(getattr(self.cls, attr)))

        return controller_namespace.route(controller_route)(self.cls)

    def find_namespace(self):
        namespace_name = self.get_namespace_name()
        founded_namespace = None
        for api_namespace in self.api.namespaces:
            if api_namespace.name == namespace_name:
                founded_namespace = api_namespace
                break
        else:
            founded_namespace = self.api.namespace(namespace_name,
                                                   description=f'{namespace_name} endpoints',
                                                   path=f'/api/{namespace_name}')
        return founded_namespace

    def get_namespace_name(self):

        root_directory = self.application_config.root_directory
        controllers_path = os.path.join(root_directory, 'controllers')
        module_name = self.cls.__module__
        module_path = sys.modules[module_name].__file__
        path_of_controllers = os.path.join(controllers_path, '')
        namespace_folder = module_path.replace(path_of_controllers, '')
        split_namespace = Utils.path_split(namespace_folder)
        if len(split_namespace) > 1:
            name = split_namespace[0].title()
        else:
            name = self.cls.__name__.replace(
                'Controllers', '').replace('Resource', '')
        return name

    def find_route(self):
        namespace_name = self.get_namespace_name()
        route_path = self.cls.__name__.replace(
            'Resource', '').replace(namespace_name, '')
        return f'/{route_path}' if route_path is not None and route_path != '' else ''


def controller(namespace=None, route=None):
    def decorate(cls):
        application_config = DependencyContainer.Instance.config_manager.get(
            ApplicationConfig)
        if sys.modules[cls.__module__].__file__.startswith(application_config.root_directory):

            api = DependencyContainer.Instance.api

            con = Controller(
                cls=cls, api=api, application_config=application_config, namespace=namespace, route=route)
            return con.create_route()

    return decorate
