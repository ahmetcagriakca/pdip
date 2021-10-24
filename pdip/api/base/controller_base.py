import os
import sys

from .endpoint_base import endpoint
from ...utils.utils import Utils
from ...configuration.models.application import ApplicationConfig


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

        decorator = endpoint(namespace=controller_namespace, api=self.api)
        for attr in self.cls.__dict__:
            if callable(getattr(self.cls, attr)) and attr in self.white_list:
                func_attr = getattr(self.cls, attr)
                if hasattr(func_attr, 'decorated') and func_attr.decorated:
                    continue
                setattr(self.cls, attr, decorator(func_attr))

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
        excluded_namespace_names = ['controllers', 'Controllers']
        path_of_root = os.path.join(self.application_config.root_directory, '')
        module_name = self.cls.__module__
        module_path = sys.modules[module_name].__file__
        namespace_folder = module_path.replace(path_of_root, '')
        split_namespace = Utils.path_split(namespace_folder)
        for excluded_namespace_name in excluded_namespace_names:
            if excluded_namespace_name in split_namespace:
                split_namespace.remove(excluded_namespace_name)
        if len(split_namespace) > 1:
            name = split_namespace[0].title()
        else:
            name = self.cls.__name__.replace(
                'Controller', '').replace('Resource', '')
        return name

    def find_route(self):
        namespace_name = self.get_namespace_name()
        route_path = self.cls.__name__.replace(
            'Resource', '').replace(namespace_name, '')
        return f'/{route_path}' if route_path is not None and route_path != '' else ''
