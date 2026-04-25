"""Unit tests for ``ConnectionSourceAdapterFactory``.

The source factory mirrors the target factory, minus the ``InMemory``
branch. We assert each routing case, each ``isinstance`` failure, and
the currently-broken ``File`` / ``Queue`` paths (attributes never
populated by ``__init__`` — see module docstring on the target
factory test for the real-bug note).
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402

from pdip.exceptions import (  # noqa: E402
    IncompatibleAdapterException,
    NotSupportedFeatureException,
)
from pdip.integrator.connection.base import ConnectionSourceAdapter  # noqa: E402
from pdip.integrator.connection.domain.enums import ConnectionTypes  # noqa: E402
from pdip.integrator.connection.factories.connection_source_adapter_factory import (  # noqa: E402
    ConnectionSourceAdapterFactory,
)


def _build_factory(sql=None, big_data=None, web_service=None):
    sql = sql if sql is not None else MagicMock(spec=ConnectionSourceAdapter)
    big_data = (
        big_data if big_data is not None else MagicMock(spec=ConnectionSourceAdapter)
    )
    web_service = (
        web_service
        if web_service is not None
        else MagicMock(spec=ConnectionSourceAdapter)
    )
    return ConnectionSourceAdapterFactory(
        sql_source_adapter=sql,
        big_data_source_adapter=big_data,
        web_service_source_adapter=web_service,
    )


class ConnectionSourceAdapterFactoryRoutesBySupportedType(TestCase):
    def test_sql_type_returns_the_sql_adapter_instance(self):
        sql_adapter = MagicMock(spec=ConnectionSourceAdapter, name="sql")
        factory = _build_factory(sql=sql_adapter)

        result = factory.get_adapter(ConnectionTypes.Sql)

        self.assertIs(result, sql_adapter)

    def test_bigdata_type_returns_the_bigdata_adapter_instance(self):
        big_data_adapter = MagicMock(spec=ConnectionSourceAdapter, name="bigdata")
        factory = _build_factory(big_data=big_data_adapter)

        result = factory.get_adapter(ConnectionTypes.BigData)

        self.assertIs(result, big_data_adapter)

    def test_webservice_type_returns_the_webservice_adapter_instance(self):
        web_service_adapter = MagicMock(
            spec=ConnectionSourceAdapter, name="web_service"
        )
        factory = _build_factory(web_service=web_service_adapter)

        result = factory.get_adapter(ConnectionTypes.WebService)

        self.assertIs(result, web_service_adapter)


class ConnectionSourceAdapterFactoryRejectsIncompatibleSlot(TestCase):
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


class ConnectionSourceAdapterFactoryUnsupportedPaths(TestCase):
    """``File`` / ``Queue`` source adapters are not wired in this
    build: the factory raises ``NotSupportedFeatureException``
    instead of leaking the prior ``AttributeError`` from the missing
    slot."""

    def test_file_type_raises_not_supported_feature(self):
        factory = _build_factory()

        with self.assertRaises(NotSupportedFeatureException) as ctx:
            factory.get_adapter(ConnectionTypes.File)

        self.assertIn("File", str(ctx.exception))

    def test_queue_type_raises_not_supported_feature(self):
        factory = _build_factory()

        with self.assertRaises(NotSupportedFeatureException) as ctx:
            factory.get_adapter(ConnectionTypes.Queue)

        self.assertIn("Queue", str(ctx.exception))


class ConnectionSourceAdapterFactoryRejectsUnknownType(TestCase):
    def test_unknown_enum_value_raises_not_supported(self):
        factory = _build_factory()

        class _Fake:
            name = "Unknown"

            def __eq__(self, other):
                return False

        with self.assertRaises(NotSupportedFeatureException):
            factory.get_adapter(_Fake())


class ConnectionSourceAdapterFactoryAsyncBranch(TestCase):
    """ADR-0032 §3 — ``is_async=True`` must (a) verify the
    ``pdip[async]`` extra is installed (clean ImportError otherwise)
    and (b) raise ``NotSupportedFeatureException`` for every connection
    type until the matching async sibling adapter lands. The check
    runs before any sibling lookup so the failure mode is the same
    for every type."""

    def test_is_async_true_raises_import_error_when_extra_missing(self):
        factory = _build_factory()
        with patch(
            "pdip.integrator.connection.factories"
            ".connection_source_adapter_factory.require_async_extra",
            side_effect=ImportError(
                "install ``pdip[async]`` to use async adapters"
            ),
        ):
            with self.assertRaises(ImportError) as ctx:
                factory.get_adapter(ConnectionTypes.Sql, is_async=True)
        self.assertIn("pdip[async]", str(ctx.exception))

    def test_is_async_true_with_extra_present_raises_not_supported(self):
        factory = _build_factory()
        with patch(
            "pdip.integrator.connection.factories"
            ".connection_source_adapter_factory.require_async_extra",
            return_value=None,
        ):
            with self.assertRaises(NotSupportedFeatureException) as ctx:
                factory.get_adapter(ConnectionTypes.Sql, is_async=True)
        self.assertIn("async", str(ctx.exception).lower())

    def test_is_async_default_false_keeps_existing_sync_routing(self):
        sql_adapter = MagicMock(spec=ConnectionSourceAdapter, name="sql")
        factory = _build_factory(sql=sql_adapter)

        # Default ``is_async=False`` must not invoke the async-extra
        # check at all — the sync routing is unchanged.
        with patch(
            "pdip.integrator.connection.factories"
            ".connection_source_adapter_factory.require_async_extra",
            side_effect=AssertionError("must not be called for sync"),
        ):
            result = factory.get_adapter(ConnectionTypes.Sql)
        self.assertIs(result, sql_adapter)
