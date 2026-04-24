import os
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

        os.environ["PYTHON_ENVIRONMENT"] = ""
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


class TestConfigManagerEnvironmentOverride(TestCase):
    """Environment variables of the form {CLASS_SNAKE_UPPER}_{PROP_SNAKE_UPPER}
    take precedence over YAML values. See ADR-0005."""

    def setUp(self):
        self.root_directory = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__))))
        self.module_finder = ModuleFinder(root_directory=self.root_directory)

    def tearDown(self):
        if hasattr(self, 'module_finder') and self.module_finder is not None:
            self.module_finder.cleanup()
            del self.module_finder
        os.environ.pop("APPLICATION_NAME", None)
        os.environ["PYTHON_ENVIRONMENT"] = ""
        return super().tearDown()

    def test_environment_variable_overrides_yaml_value(self):
        os.environ["APPLICATION_NAME"] = "FROM_ENV"
        config_manager = ConfigManager(
            root_directory=self.root_directory,
            module_finder=self.module_finder,
        )
        self.assertEqual(
            config_manager.get(ApplicationConfig).name, "FROM_ENV"
        )

    def test_missing_environment_variable_falls_through_to_yaml(self):
        # Make sure the var is not leaking from a previous test.
        os.environ.pop("APPLICATION_NAME", None)
        config_manager = ConfigManager(
            root_directory=self.root_directory,
            module_finder=self.module_finder,
        )
        self.assertEqual(config_manager.get(ApplicationConfig).name, "APP")
