import inspect
import os
from typing import TypeVar, Type

from ..configuration.models.application import ApplicationConfig
from ..dependency.container import DependencyContainer

T = TypeVar('T')


class Pdi(object):
    def __init__(self,
                 root_directory: str = None,
                 configurations: [] = None,
                 excluded_modules: [] = None,
                 initialize_flask: bool = True
                 ):
        if root_directory is None:
            stack = inspect.stack()
            root_directory = self.get_root_directory(stack)
        self.excluded_modules = excluded_modules
        self.configurations = configurations
        self.root_directory = root_directory
        if DependencyContainer.Instance is None:
            DependencyContainer.initialize_service(root_directory=root_directory,
                                                   configurations=configurations,
                                                   excluded_modules=excluded_modules,
                                                   initialize_flask=initialize_flask)

    def cleanup(self):
        if DependencyContainer is not None:
            DependencyContainer.cleanup()

    def get_root_directory(self, stack):
        file_path = stack[1].filename
        directory = os.path.dirname(os.path.realpath(file_path))
        return directory

    def get(self, instance_type: Type[T]) -> T:
        return DependencyContainer.Instance.get(instance_type)

    def set_secret_key(self, key):
        DependencyContainer.Instance.config_manager.set(
            ApplicationConfig, 'secret_key', key)
