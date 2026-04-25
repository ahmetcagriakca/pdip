"""Unit tests for ``AsyncIntegrationExecute`` (ADR-0032 §4).

The async sibling of ``IntegrationSourceToTargetExecuteStrategy``
declares ``async def execute`` as its abstract method. These tests
mirror the ``test_strategy_base_contract`` shape for the sync ABC:
(a) the method is a coroutine function so callers ``await`` rather
than expect a sync return, (b) the abstract body executed via
``await super().execute(...)`` returns ``None`` — pinning the
contract lines so a regression on the abstract signature is caught
in unit tests without booting a real async backend.
"""

import asyncio
import inspect
from unittest import TestCase
from unittest.mock import MagicMock

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from pdip.integrator.integration.types.sourcetotarget.strategies.async_.base import (  # noqa: E402
    AsyncIntegrationExecute,
)


class _ConcreteAsyncStrategy(AsyncIntegrationExecute):
    async def execute(self, operation_integration, channel):
        return await super().execute(operation_integration, channel)


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


class AsyncIntegrationExecuteShape(TestCase):
    def test_execute_is_a_coroutine_function(self):
        self.assertTrue(
            inspect.iscoroutinefunction(AsyncIntegrationExecute.execute)
        )


class AsyncIntegrationExecuteAbstractStubReturnsNone(TestCase):
    def test_super_call_returns_none(self):
        strategy = _ConcreteAsyncStrategy()

        result = _run(
            strategy.execute(
                operation_integration=MagicMock(name="op"),
                channel=MagicMock(name="channel"),
            )
        )

        self.assertIsNone(result)
