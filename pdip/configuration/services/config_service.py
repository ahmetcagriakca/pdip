from functools import lru_cache
from pdip.exceptions.required_class_exception import RequiredClassException

from injector import inject

from .config_parameter import ConfigParameter
from pdip.data import RepositoryProvider
from pdip.dependency import IScoped


class ConfigService(IScoped):
    @inject
    def __init__(self,
                 repository_provider: RepositoryProvider
                 ):
        self.repository_provider = repository_provider
        config_subclasses= ConfigParameter.__subclasses__()
        if  config_subclasses is None or len(config_subclasses)==0:
            raise RequiredClassException(f'Requires {ConfigParameter.__name__} derived class')
        config_class = config_subclasses[0]
        self.config_reposiotry = repository_provider.get(config_class)

    @lru_cache()
    def get_config_by_name(self, name):
        parameter = self.config_reposiotry.first(Name=name)
        if parameter is not None:
            return parameter.Value
        else:
            return None
