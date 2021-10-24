import os
import sys

from unittest import TestCase
from pdip.configuration import ConfigManager
from pdip.configuration.models.application import ApplicationConfig
from pdip.utils import ModuleFinder


class TestConfigManager(TestCase):
    def setUp(self):
        try:
            self.root_directory = os.path.abspath(os.path.join(
                os.path.dirname(os.path.abspath(__file__))))
            self.module_finder = ModuleFinder(root_directory=self.root_directory)
            self.config_manager = None
        except:
            self.tearDown()
            raise

    def tearDown(self):
        if hasattr(self, 'module_finder') and self.module_finder is not None:
            self.module_finder.cleanup()
            del self.module_finder
        modules = [y for y in sys.modules if 'pdip' in y]
        for module in modules:
            del module
        return super().tearDown()

    def test_FindConfiguration(self):
        self.config_manager = ConfigManager(
            root_directory=self.root_directory, module_finder=self.module_finder)
        result = self.config_manager.get_all()
        assert len(result) > 0
        application_config = self.config_manager.get(ApplicationConfig)
        assert application_config.name == 'APP'

    def test_FindConfigurationWithEnvironment(self):
        os.environ["PYTHON_ENVIRONMENT"] = "test"
        self.config_manager = ConfigManager(
            root_directory=self.root_directory, module_finder=self.module_finder)
        result = self.config_manager.get_all()
        assert len(result) > 0
        application_config = self.config_manager.get(ApplicationConfig)
        assert application_config.name == 'TEST_APP'

    def test_SetConfiguration(self):
        self.config_manager = ConfigManager(
            root_directory=self.root_directory, module_finder=self.module_finder)
        hostname = os.getenv('HOSTNAME', '')
        self.config_manager.set(ApplicationConfig, "hostname", hostname)

        assert self.config_manager.get(ApplicationConfig).hostname == hostname
