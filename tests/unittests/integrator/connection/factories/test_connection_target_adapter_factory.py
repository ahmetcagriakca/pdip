"""Unit tests for ``ConnectionTargetAdapterFactory``.

The factory returns one of its injected adapters keyed on the
``ConnectionTypes`` enum. It raises ``IncompatibleAdapterException``
when the candidate adapter does not implement
``ConnectionTargetAdapter``, and ``NotSupportedFeatureException`` when
asked for a type it does not know how to route.

These tests pin down:

* each supported connection type routes to the matching adapter,
* the ``isinstance`` guard raises ``IncompatibleAdapterException``
  when a registered slot holds a non-adapter object,
* unknown enum values raise ``NotSupportedFeatureException``,
* the ``File`` / ``Queue`` / ``InMemory`` branches reference
  attributes that the ``__init__`` never sets — they raise
  ``AttributeError`` in the current implementation. We record that
  as a **real bug** (see README note) but still assert the
  observable behaviour.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.exceptions import (  # noqa: E402
    IncompatibleAdapterException,
    NotSupportedFeatureException,
)
from pdip.integrator.connection.base import ConnectionTargetAdapter  # noqa: E402
from pdip.integrator.connection.domain.enums import ConnectionTypes  # noqa: E402
from pdip.integrator.connection.factories.connection_target_adapter_factory import (  # noqa: E402
    ConnectionTargetAdapterFactory,
)


def _build_factory(sql=None, big_data=None, web_service=None):
    """Return a factory with adapter slots filled by mocks that pass
    ``isinstance(..., ConnectionTargetAdapter)`` unless the caller
    overrides them."""
    sql = sql if sql is not None else MagicMock(spec=ConnectionTargetAdapter)
    big_data = (
        big_data if big_data is not None else MagicMock(spec=ConnectionTargetAdapter)
    )
    web_service = (
        web_service
        if web_service is not None
        else MagicMock(spec=ConnectionTargetAdapter)
    )
    return ConnectionTargetAdapterFactory(
        sql_target_adapter=sql,
        big_data_target_adapter=big_data,
        web_service_target_adapter=web_service,
    )


class ConnectionTargetAdapterFactoryRoutesBySupportedType(TestCase):
    def test_sql_type_returns_the_sql_adapter_instance(self):
        sql_adapter = MagicMock(spec=ConnectionTargetAdapter, name="sql")
        factory = _build_factory(sql=sql_adapter)

        result = factory.get_adapter(ConnectionTypes.Sql)

        self.assertIs(result, sql_adapter)

    def test_bigdata_type_returns_the_bigdata_adapter_instance(self):
        big_data_adapter = MagicMock(spec=ConnectionTargetAdapter, name="bigdata")
        factory = _build_factory(big_data=big_data_adapter)

        result = factory.get_adapter(ConnectionTypes.BigData)

        self.assertIs(result, big_data_adapter)

    def test_webservice_type_returns_the_webservice_adapter_instance(self):
        web_service_adapter = MagicMock(
            spec=ConnectionTargetAdapter, name="web_service"
        )
        factory = _build_factory(web_service=web_service_adapter)

        result = factory.get_adapter(ConnectionTypes.WebService)

        self.assertIs(result, web_service_adapter)


class ConnectionTargetAdapterFactoryRejectsIncompatibleSlot(TestCase):
    def test_sql_slot_filled_with_non_adapter_raises_incompatible(self):
        factory = _build_factory(sql=object())

        with self.assertRaises(IncompatibleAdapterException):
            factory.get_adapter(ConnectionTypes.Sql)

    def test_bigdata_slot_filled_with_non_adapter_raises_incompatible(self):
        factory = _build_factory(big_data=object())

        with self.assertRaises(IncompatibleAdapterException):
            factory.get_adapter(ConnectionTypes.BigData)

    def test_webservice_slot_filled_with_non_adapter_raises_incompatible(self):
        factory = _build_factory(web_service=object())

        with self.assertRaises(IncompatibleAdapterException):
            factory.get_adapter(ConnectionTypes.WebService)


class ConnectionTargetAdapterFactoryUnsupportedPaths(TestCase):
    """``File`` / ``Queue`` / ``InMemory`` reference attributes that
    ``__init__`` never assigns. Today they raise ``AttributeError``
    rather than a friendlier ``NotSupportedFeatureException`` — see
    the module docstring. We pin down the current behaviour so any
    future fix (which should switch them to raise
    ``NotSupportedFeatureException``) is a deliberate test update,
    not a silent change."""

    def test_file_type_raises_attribute_error_today(self):
        factory = _build_factory()

        with self.assertRaises(AttributeError):
            factory.get_adapter(ConnectionTypes.File)

    def test_queue_type_raises_attribute_error_today(self):
        factory = _build_factory()

        with self.assertRaises(AttributeError):
            factory.get_adapter(ConnectionTypes.Queue)

    def test_in_memory_type_raises_attribute_error_today(self):
        factory = _build_factory()

        with self.assertRaises(AttributeError):
            factory.get_adapter(ConnectionTypes.InMemory)


class ConnectionTargetAdapterFactoryRejectsUnknownType(TestCase):
    def test_unknown_enum_value_raises_not_supported(self):
        # Enum.__call__ accepts only registered values, so we use a
        # stand-in object whose equality checks all miss the known
        # branches — that exercises the final ``else`` clause.
        factory = _build_factory()

        class _Fake:
            name = "Unknown"

            def __eq__(self, other):
                return False

        with self.assertRaises(NotSupportedFeatureException):
            factory.get_adapter(_Fake())
