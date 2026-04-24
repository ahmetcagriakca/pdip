import os
import tempfile
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
        except Exception:
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


class ConfigManagerLookupByName(TestCase):
    """``get_by_name`` walks the flat ``configs`` list and returns the
    first ``instance`` whose ``name`` matches. It covers both typed
    ``BaseConfig`` subclasses and untyped loose-dict entries."""

    def setUp(self):
        self.root_directory = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)))
        )
        self.module_finder = ModuleFinder(root_directory=self.root_directory)
        self.config_manager = ConfigManager(
            root_directory=self.root_directory,
            module_finder=self.module_finder,
        )

    def tearDown(self):
        self.module_finder.cleanup()
        os.environ["PYTHON_ENVIRONMENT"] = ""
        return super().tearDown()

    def test_get_by_name_returns_instance_for_known_name(self):
        # ``ApplicationConfig`` is registered under its de-suffixed
        # class name, ``Application``.
        result = self.config_manager.get_by_name("Application")
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "APP")

    def test_get_by_name_returns_none_for_unknown_name(self):
        self.assertIsNone(self.config_manager.get_by_name("DOES_NOT_EXIST"))


class ConfigManagerFallsBackToGlobbedYaml(TestCase):
    """When neither ``application.yml`` nor
    ``application.<env>.yml`` exists at the root, ``ConfigManager``
    falls back to the first file matching ``application.*.yml``."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="pdip-cfg-")
        yml_path = os.path.join(self._tmp, "application.fallback.yml")
        with open(yml_path, "w") as fh:
            fh.write("APPLICATION:\n  NAME: FALLBACK\n")
        self.module_finder = ModuleFinder(root_directory=self._tmp)
        # Env var would shadow the glob behaviour; keep it off.
        os.environ["PYTHON_ENVIRONMENT"] = ""

    def tearDown(self):
        self.module_finder.cleanup()
        # best-effort cleanup; files may have been added during the run
        for name in os.listdir(self._tmp):
            try:
                os.remove(os.path.join(self._tmp, name))
            except OSError:
                pass
        try:
            os.rmdir(self._tmp)
        except OSError:
            pass
        return super().tearDown()

    def test_picks_first_globbed_yaml_when_primary_missing(self):
        manager = ConfigManager(
            root_directory=self._tmp, module_finder=self.module_finder
        )
        self.assertEqual(manager.get(ApplicationConfig).name, "FALLBACK")


class ConfigManagerKeepsLooseYamlKeys(TestCase):
    """Top-level YAML keys that don't match any registered
    ``BaseConfig`` subclass are preserved as untyped dict entries in
    ``configs`` so consumers can fetch them by name."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="pdip-cfg-")
        yml_path = os.path.join(self._tmp, "application.yml")
        with open(yml_path, "w") as fh:
            fh.write(
                "APPLICATION:\n  NAME: APP\nFEATURE_FLAGS:\n  TOGGLE: true\n"
            )
        self.module_finder = ModuleFinder(root_directory=self._tmp)
        os.environ["PYTHON_ENVIRONMENT"] = ""

    def tearDown(self):
        self.module_finder.cleanup()
        for name in os.listdir(self._tmp):
            try:
                os.remove(os.path.join(self._tmp, name))
            except OSError:
                pass
        try:
            os.rmdir(self._tmp)
        except OSError:
            pass
        return super().tearDown()

    def test_loose_key_is_preserved_as_untyped_config(self):
        manager = ConfigManager(
            root_directory=self._tmp, module_finder=self.module_finder
        )

        loose = manager.get_by_name("FEATURE_FLAGS")

        self.assertIsInstance(loose, dict)
        self.assertEqual(loose.get("TOGGLE"), True)

    def test_loose_key_is_not_returned_by_typed_lookup(self):
        manager = ConfigManager(
            root_directory=self._tmp, module_finder=self.module_finder
        )

        typed_only = manager.get_all_type_configs()
        typed_names = [c["name"] for c in typed_only]
        self.assertNotIn("FEATURE_FLAGS", typed_names)
