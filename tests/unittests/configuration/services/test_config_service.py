"""Unit tests for ``pdip.configuration.services.config_service.ConfigService``.

The service discovers a single subclass of ``ConfigParameterBase`` at
construction time and uses it as the repository entity. It then looks
up individual config entries by name and caches the result. These
tests patch ``ConfigParameterBase.__subclasses__`` so a real database
is not required.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from pdip.configuration.services.config_parameter_base import ConfigParameterBase
from pdip.configuration.services.config_service import ConfigService
from pdip.exceptions import RequiredClassException


class _FakeConfigParameter(ConfigParameterBase):
    # Subclass exists only for the tests that patch the subclasses
    # list. It must be constructible with no args.
    pass


def _build_service_with_stub_subclass(first_result):
    repository_provider = MagicMock(name="RepositoryProvider")
    config_repository = MagicMock(name="ConfigRepository")
    config_repository.first.return_value = first_result
    repository_provider.get.return_value = config_repository

    with patch.object(
        ConfigParameterBase,
        "__subclasses__",
        return_value=[_FakeConfigParameter],
    ):
        service = ConfigService(repository_provider=repository_provider)
    return service, repository_provider, config_repository


class ConfigServiceLoadsConfigClass(TestCase):
    def test_init_resolves_repository_for_first_subclass(self):
        service, repository_provider, config_repository = (
            _build_service_with_stub_subclass(first_result=None)
        )

        repository_provider.get.assert_called_once_with(_FakeConfigParameter)
        self.assertIs(service.config_reposiotry, config_repository)

    def test_init_raises_required_class_exception_when_no_subclass_registered(self):
        repository_provider = MagicMock(name="RepositoryProvider")

        with patch.object(
            ConfigParameterBase, "__subclasses__", return_value=[]
        ):
            with self.assertRaises(RequiredClassException):
                ConfigService(repository_provider=repository_provider)

    def test_init_raises_required_class_exception_when_subclasses_is_none(self):
        repository_provider = MagicMock(name="RepositoryProvider")

        with patch.object(
            ConfigParameterBase, "__subclasses__", return_value=None
        ):
            with self.assertRaises(RequiredClassException):
                ConfigService(repository_provider=repository_provider)


class ConfigServiceLooksUpValues(TestCase):
    def test_get_config_by_name_returns_value_when_found(self):
        parameter = MagicMock()
        parameter.Value = "super-secret"
        service, _, config_repository = _build_service_with_stub_subclass(
            first_result=parameter,
        )

        result = service.get_config_by_name("api_key")

        config_repository.first.assert_called_once_with(Name="api_key")
        self.assertEqual(result, "super-secret")

    def test_get_config_by_name_returns_none_when_missing(self):
        service, _, config_repository = _build_service_with_stub_subclass(
            first_result=None,
        )

        result = service.get_config_by_name("absent")

        config_repository.first.assert_called_once_with(Name="absent")
        self.assertIsNone(result)

    def test_get_config_by_name_caches_repeated_lookups(self):
        parameter = MagicMock()
        parameter.Value = "cached"
        service, _, config_repository = _build_service_with_stub_subclass(
            first_result=parameter,
        )

        service.get_config_by_name("k")
        service.get_config_by_name("k")

        # lru_cache collapses repeated calls into one repository hit.
        self.assertEqual(config_repository.first.call_count, 1)
