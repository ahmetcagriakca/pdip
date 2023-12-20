import os
from typing import List, Type, TypeVar

import yaml

from .models.base.base_config import BaseConfig
from ..utils import Utils, ModuleFinder

T = TypeVar('T')


class ConfigManager:
    def __init__(self, root_directory: str, module_finder: ModuleFinder) -> None:
        # Create an empty list with items of type T
        self.module_finder = module_finder
        self.configs = self.__get_configs(root_directory)

    def get_by_name(self, name):
        for config in self.configs:
            if config["name"] == name:
                return config.get("instance")

    def get_all(self):
        return self.configs

    def get_all_type_configs(self):
        return [c for c in self.configs if c["type"] is not None]

    def get(self, generic_type: Type[T]) -> T:
        for config in self.configs:
            config_type = config.get("type")
            if config_type is not None and (isinstance(config.get("instance"),
                          generic_type) or config_type is generic_type or generic_type.__module__ == config_type.__module__):
                return config.get("instance")

    def set(self, generic_type, instance_property, property_value):
        config_instance = self.get(generic_type=generic_type)
        if config_instance is None:
            config_instance = generic_type()
            self.configs.append({"type": generic_type, "instance": config_instance})
        setattr(config_instance, instance_property, property_value)

    def __get_configs(self, root_directory: str) -> List[dict]:
        self.module_finder.import_modules_by_name_ends_with(name='Configs')

        environment = os.getenv('PYTHON_ENVIRONMENT', None)
        config_name = "application.yml"
        if environment is not None and environment != '':
            config_name_split = "application.yml".split('.')
            config_name = f'{config_name_split[0]}.{environment}.{config_name_split[1]}'
        config_path = os.path.join(root_directory, config_name)
        configs: List[dict] = []
        if os.path.exists(config_path):
            with open(config_path, 'r') as yml_file:
                loaded_configs = yaml.load(yml_file, Loader=yaml.FullLoader)
            for config in BaseConfig.__subclasses__():
                config_instance = config()
                class_name, class_sneak_name = Utils.get_config_name(config_instance.__class__.__name__)
                search_class_in_configs = [class_name, class_sneak_name, class_name.upper(), class_sneak_name.upper()]
                class_properties = [a for a in dir(
                    config_instance) if not (a.startswith('_'))]
                loaded_config=None
                for search_in_config in search_class_in_configs:
                    if search_in_config in loaded_configs:
                        loaded_config = loaded_configs[search_in_config]
                        break
                if loaded_config is None:
                    continue
                for prop in class_properties:
                    config_value = None
                    property_name, property_snake_name = Utils.get_property_name(prop)
                    search_property_in_configs = [property_name, property_snake_name, property_name.upper(),
                                                  property_snake_name.upper()]

                    for search_property_in_config in search_property_in_configs:
                        if search_property_in_config in loaded_config:
                            config_value = loaded_config[search_property_in_config]
                            break
                    if property_snake_name.upper() == 'ROOT_DIRECTORY':
                        config_value = root_directory

                    environment_name = f'{class_sneak_name.upper()}_{property_snake_name.upper()}'
                    property_value = os.getenv(environment_name, config_value)
                    setattr(config_instance, prop, property_value)
                configs.append({"name": class_name, "type": config, "instance": config_instance})
            for key in loaded_configs.keys():
                has_key = False
                class_name, class_sneak_name = Utils.get_config_name(key)
                search_class_in_configs = [class_name, class_sneak_name, class_name.upper(), class_sneak_name.upper()]

                for conf in configs:
                    config_name, config_sneak_name = Utils.get_config_name(conf["name"])
                    config_names = [config_name, config_sneak_name, config_name.upper(), config_sneak_name.upper()]
                    for search_class_in_config in search_class_in_configs:
                        if search_class_in_config in config_names:
                            has_key = True
                            break

                if not has_key:
                    configs.append({"name": key, "type": None, "instance": loaded_configs[key]})
        return configs
