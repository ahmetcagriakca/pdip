import os
from typing import List, Type, TypeVar

import yaml
from ..utils import Utils, ModuleFinder
from .models.base_config import BaseConfig

T = TypeVar('T')


class ConfigManager:
    def __init__(self, root_directory: str, module_finder: ModuleFinder) -> None:
        # Create an empty list with items of type T
        self.module_finder = module_finder
        self.configs = self.__get_configs(root_directory)

    def get_all(self):
        return self.configs

    def get(self, generic_type: Type[T]) -> T:
        for config in self.configs:
            config_type = config.get("type")
            if config_type is generic_type:
                return config.get("instance")

    def set(self, generic_type, instance_property, property_value):
        config_instance = self.get(generic_type=generic_type)
        setattr(config_instance, instance_property, property_value)

    def empty(self) -> bool:
        return not self.items

    def __get_configs(self, root_directory: str) -> List[dict]:
        self.module_finder.import_modules_by_name_ends_with(name='Configs')

        environment = os.getenv('PYTHON_ENVIRONMENT', None)
        config_name = "application.yml"
        if environment is not None:
            config_name_split = "application.yml".split('.')
            config_name = f'{config_name_split[0]}.{environment}.{config_name_split[1]}'
        config_path=os.path.join(root_directory, config_name)
        print(config_path)
        configs: List[dict] = []
        if os.path.exists(config_path):
            with open(config_path, 'r') as yml_file:
                loaded_configs = yaml.load(yml_file, Loader=yaml.FullLoader)
            for config in BaseConfig.__subclasses__():
                config_instance = config()
                class_name = Utils.get_config_name(
                    config_instance.__class__.__name__)
                class_properties = [a for a in dir(
                    config_instance) if not (a.startswith('_'))]
                for prop in class_properties:
                    property_name = prop.upper()
                    if class_name in loaded_configs:
                        loaded_config = loaded_configs[class_name]
                        if property_name in loaded_config:
                            config_value = loaded_config[property_name]
                        elif property_name == 'ROOT_DIRECTORY':
                            config_value = root_directory
                        else:
                            config_value = None
                    else:
                        config_value = None

                    environment_name = f'{class_name}_{property_name}'
                    property_value = os.getenv(environment_name, config_value)
                    setattr(config_instance, prop, property_value)
                configs.append({"type": config, "instance": config_instance})
        return configs
