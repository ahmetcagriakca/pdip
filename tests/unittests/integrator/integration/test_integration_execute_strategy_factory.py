"""Unit tests for ``IntegrationSourceToTargetExecuteStrategyFactory``.

The factory picks between the single-process and parallel-thread
strategies based on the ``process_count`` argument:

* ``None`` or ``<= 1`` -> single-process strategy,
* ``> 1``              -> parallel-thread strategy.

Compatibility with the abstract ``IntegrationSourceToTargetExecuteStrategy``
is enforced by an ``isinstance`` guard on both branches.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.exceptions import (  # noqa: E402
    IncompatibleAdapterException,
    NotSupportedFeatureException,
)
from pdip.integrator.integration.types.sourcetotarget.strategies.base import (  # noqa: E402
    IntegrationSourceToTargetExecuteStrategy,
)
from pdip.integrator.integration.types.sourcetotarget.strategies.factories.integration_execute_strategy_factory import (  # noqa: E402
    IntegrationSourceToTargetExecuteStrategyFactory,
)


def _build_factory(parallel=None, single=None):
    parallel = (
        parallel
        if parallel is not None
        else MagicMock(spec=IntegrationSourceToTargetExecuteStrategy, name="parallel")
    )
    single = (
        single
        if single is not None
        else MagicMock(spec=IntegrationSourceToTargetExecuteStrategy, name="single")
    )
    return IntegrationSourceToTargetExecuteStrategyFactory(
        parallel_thread_integration_execute=parallel,
        single_process_integration_execute=single,
    )


class StrategyFactoryRoutesByProcessCount(TestCase):
    def test_none_process_count_selects_single_process(self):
        single = MagicMock(spec=IntegrationSourceToTargetExecuteStrategy, name="s")
        factory = _build_factory(single=single)

        result = factory.get(process_count=None)

        self.assertIs(result, single)

    def test_process_count_one_selects_single_process(self):
        single = MagicMock(spec=IntegrationSourceToTargetExecuteStrategy, name="s")
        factory = _build_factory(single=single)

        result = factory.get(process_count=1)

        self.assertIs(result, single)

    def test_process_count_greater_than_one_selects_parallel(self):
        parallel = MagicMock(spec=IntegrationSourceToTargetExecuteStrategy, name="p")
        factory = _build_factory(parallel=parallel)

        result = factory.get(process_count=4)

        self.assertIs(result, parallel)


class StrategyFactoryRejectsIncompatibleStrategies(TestCase):
    def test_parallel_slot_incompatible_raises_when_process_count_exceeds_one(self):
        factory = _build_factory(parallel=object())

        with self.assertRaises(IncompatibleAdapterException):
            factory.get(process_count=2)

    def test_single_slot_incompatible_raises_when_process_count_is_one(self):
        factory = _build_factory(single=object())

        with self.assertRaises(IncompatibleAdapterException):
            factory.get(process_count=1)


class StrategyFactoryAsyncBranch(TestCase):
    """ADR-0032 §4 — ``is_async=True`` is the configuration entry
    point for the new async strategy. The concrete
    ``AsyncIntegrationExecute`` implementation requires asyncpg /
    aiomysql / aioodbc-backed adapters that are queued as a
    follow-up; until those land, the factory raises
    ``NotSupportedFeatureException`` so the caller fails fast and
    diagnosable instead of silently falling back to the sync
    strategy."""

    def test_is_async_true_raises_not_supported_with_pointer_to_adr(self):
        factory = _build_factory()

        with self.assertRaises(NotSupportedFeatureException) as ctx:
            factory.get(process_count=None, is_async=True)

        message = str(ctx.exception)
        self.assertIn("async", message.lower())
        self.assertIn("ADR-0032", message)

    def test_is_async_true_independent_of_process_count(self):
        # Asking for async mode must short-circuit the
        # process_count branch — the failure mode is the same
        # regardless of how many processes were requested.
        factory = _build_factory()

        for pc in (None, 1, 4):
            with self.assertRaises(NotSupportedFeatureException):
                factory.get(process_count=pc, is_async=True)

    def test_is_async_default_false_keeps_existing_sync_routing(self):
        single = MagicMock(
            spec=IntegrationSourceToTargetExecuteStrategy, name="s"
        )
        factory = _build_factory(single=single)

        # Default ``is_async=False`` must not change anything: the
        # legacy ``process_count`` switch keeps routing.
        result = factory.get(process_count=None)

        self.assertIs(result, single)
