import os

from unittest import TestCase
from pdi.configuration import ConfigManager
from pdi.configuration.models import ApplicationConfig
from pdi.utils import ModuleFinder


class TestConfigManager(TestCase):
    def test_FindConfiguration(self):
        root_directory = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__))))
        module_finder = ModuleFinder(root_directory=root_directory)
        config_manager = ConfigManager(
            root_directory=root_directory, module_finder=module_finder)
        result = config_manager.get_all()
        assert len(result) > 0
        application_config = config_manager.get(ApplicationConfig)
        assert application_config.name == 'APP'

    def test_FindConfigurationWithEnvironment(self):
        os.environ["PYTHON_ENVIRONMENT"] = "test"
        root_directory = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__))))
        print(root_directory)
        module_finder = ModuleFinder(root_directory=root_directory)
        config_manager = ConfigManager(
            root_directory=root_directory, module_finder=module_finder)
        result = config_manager.get_all()
        assert len(result) > 0
        application_config = config_manager.get(ApplicationConfig)
        assert application_config.name == 'TEST_APP'


    def test_SetConfiguration(self):
        root_directory = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__))))
        print(root_directory)
        module_finder = ModuleFinder(root_directory=root_directory)
        config_manager = ConfigManager(
            root_directory=root_directory, module_finder=module_finder)
        hostname = os.getenv('HOSTNAME', '')
        config_manager.set(ApplicationConfig, "hostname", hostname)
        
        assert config_manager.get(ApplicationConfig).hostname==hostname