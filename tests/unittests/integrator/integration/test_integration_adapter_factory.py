"""Unit tests for ``IntegrationAdapterFactory``.

``get`` picks between a target-only adapter and a source-to-target
adapter based on the ``IntegrationBase`` shape:

* no target name -> hard ``Exception``,
* target-only (no source name) -> ``target_integration`` (if compatible),
* source and target both present -> ``source_to_target_integration``
  (guarded by an ``isinstance`` check on ``source_integration``).

After the bug fix, the ``else`` branch guards the same object it
returns (``source_to_target_integration``), so the negative path only
trips when the source-to-target adapter is itself incompatible.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.exceptions import IncompatibleAdapterException  # noqa: E402
from pdip.integrator.integration.domain.base import IntegrationBase  # noqa: E402
from pdip.integrator.integration.types.base import (  # noqa: E402
    IntegrationAdapter,
    IntegrationAdapterFactory,
)


class _TargetConn:
    def __init__(self, name):
        self.ConnectionName = name


def _make_integration(target_name, source_name=None):
    target = _TargetConn(target_name) if target_name is not None else None
    source = _TargetConn(source_name) if source_name is not None else None
    integration = IntegrationBase()
    integration.TargetConnections = target
    integration.SourceConnections = source
    return integration


def _build_factory(source=None, target=None, source_to_target=None):
    return IntegrationAdapterFactory(
        source_integration=source
        if source is not None
        else MagicMock(spec=IntegrationAdapter),
        target_integration=target
        if target is not None
        else MagicMock(spec=IntegrationAdapter),
        source_to_target_integration=source_to_target
        if source_to_target is not None
        else MagicMock(spec=IntegrationAdapter),
    )


class IntegrationAdapterFactoryRoutesByShape(TestCase):
    def test_missing_target_connections_raises(self):
        factory = _build_factory()
        integration = IntegrationBase()
        integration.TargetConnections = None

        with self.assertRaises(Exception) as ctx:
            factory.get(integration)

        self.assertIn("Target connection required", str(ctx.exception))

    def test_target_connections_without_name_raises(self):
        factory = _build_factory()
        integration = _make_integration(target_name=None)
        # Replace the None TargetConnections with an object whose
        # ``ConnectionName`` is None so we take the second half of
        # the guard.
        integration.TargetConnections = _TargetConn(None)

        with self.assertRaises(Exception) as ctx:
            factory.get(integration)

        self.assertIn("Target connection required", str(ctx.exception))

    def test_target_only_integration_returns_target_adapter(self):
        target = MagicMock(spec=IntegrationAdapter, name="target")
        factory = _build_factory(target=target)
        integration = _make_integration(target_name="T")

        result = factory.get(integration)

        self.assertIs(result, target)

    def test_source_and_target_returns_source_to_target_adapter(self):
        source_to_target = MagicMock(spec=IntegrationAdapter, name="s2t")
        factory = _build_factory(source_to_target=source_to_target)
        integration = _make_integration(target_name="T", source_name="S")

        result = factory.get(integration)

        self.assertIs(result, source_to_target)


class IntegrationAdapterFactoryRejectsIncompatibleAdapters(TestCase):
    def test_target_only_with_incompatible_target_raises(self):
        factory = _build_factory(target=object())
        integration = _make_integration(target_name="T")

        with self.assertRaises(IncompatibleAdapterException):
            factory.get(integration)

    def test_source_and_target_with_incompatible_source_to_target_raises(self):
        # The factory now guards the same object it returns: a
        # source-to-target slot that is not an ``IntegrationAdapter``
        # surfaces as ``IncompatibleAdapterException``.
        factory = _build_factory(source_to_target=object())
        integration = _make_integration(target_name="T", source_name="S")

        with self.assertRaises(IncompatibleAdapterException) as ctx:
            factory.get(integration)

        self.assertIn("incompatible", str(ctx.exception))

    def test_source_and_target_ignores_source_adapter_type_when_s2t_is_valid(self):
        # Regression: previously the guard mistakenly evaluated
        # ``source_integration`` and returned ``source_to_target``.
        # Now a broken source slot no longer blocks routing as long
        # as the returned s2t adapter is compatible.
        s2t = MagicMock(spec=IntegrationAdapter, name="s2t")
        factory = _build_factory(source=object(), source_to_target=s2t)
        integration = _make_integration(target_name="T", source_name="S")

        result = factory.get(integration)

        self.assertIs(result, s2t)
