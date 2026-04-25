"""Unit tests for the **async** connection adapter contracts (ADR-0032).

The sync ``ConnectionSourceAdapter`` and ``ConnectionTargetAdapter``
under ``pdip/integrator/connection/base/`` declare ``@abstractmethod``
stubs whose bodies are ``pass``. The async siblings introduced by
ADR-0032 mirror that shape but with ``async def`` methods, so that
callers awaiting the result get the same ``None`` from the abstract
stub that the sync caller gets today.

These tests pin (a) that the methods exist with the documented
names, (b) that they are coroutine functions (so ``await
adapter.foo(...)`` is the right calling convention), and (c) that
the bare-stub bodies execute when called via ``super()`` from a
concrete subclass — so the contract lines are covered.
"""

import asyncio
import inspect
from unittest import TestCase
from unittest.mock import MagicMock

from pdip.integrator.connection.base.async_connection_source_adapter import (
    AsyncConnectionSourceAdapter,
)
from pdip.integrator.connection.base.async_connection_target_adapter import (
    AsyncConnectionTargetAdapter,
)


# ---------------------------------------------------------------------------
# Concrete subclasses that delegate every method straight to ``super()``
# so the abstract stub bodies are actually executed.
# ---------------------------------------------------------------------------


class _ConcreteAsyncSourceAdapter(AsyncConnectionSourceAdapter):
    async def get_source_data_count(self, integration):
        return await super().get_source_data_count(integration)

    async def get_iterator(self, integration, limit):
        return await super().get_iterator(integration, limit)

    async def get_source_data_with_paging(self, integration, start, end):
        return await super().get_source_data_with_paging(
            integration, start, end
        )


class _ConcreteAsyncTargetAdapter(AsyncConnectionTargetAdapter):
    async def clear_data(self, integration):
        return await super().clear_data(integration)

    async def write_data(self, integration, source_data):
        return await super().write_data(integration, source_data)

    async def do_target_operation(self, integration):
        return await super().do_target_operation(integration)


def _run(coro):
    """Drive a coroutine to completion. Each test uses its own event
    loop instance to avoid cross-test interference."""
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Shape — the documented methods exist and are coroutine functions.
# ---------------------------------------------------------------------------


class AsyncConnectionSourceAdapterShape(TestCase):
    def test_get_source_data_count_is_a_coroutine_function(self):
        self.assertTrue(
            inspect.iscoroutinefunction(
                AsyncConnectionSourceAdapter.get_source_data_count
            )
        )

    def test_get_iterator_is_a_coroutine_function(self):
        self.assertTrue(
            inspect.iscoroutinefunction(
                AsyncConnectionSourceAdapter.get_iterator
            )
        )

    def test_get_source_data_with_paging_is_a_coroutine_function(self):
        self.assertTrue(
            inspect.iscoroutinefunction(
                AsyncConnectionSourceAdapter.get_source_data_with_paging
            )
        )


class AsyncConnectionTargetAdapterShape(TestCase):
    def test_clear_data_is_a_coroutine_function(self):
        self.assertTrue(
            inspect.iscoroutinefunction(
                AsyncConnectionTargetAdapter.clear_data
            )
        )

    def test_write_data_is_a_coroutine_function(self):
        self.assertTrue(
            inspect.iscoroutinefunction(
                AsyncConnectionTargetAdapter.write_data
            )
        )

    def test_do_target_operation_is_a_coroutine_function(self):
        self.assertTrue(
            inspect.iscoroutinefunction(
                AsyncConnectionTargetAdapter.do_target_operation
            )
        )


# ---------------------------------------------------------------------------
# Bodies — abstract stubs return ``None`` when invoked via ``super()``.
# ---------------------------------------------------------------------------


class AsyncSourceAdapterAbstractStubsReturnNone(TestCase):
    def test_get_source_data_count_stub_returns_none(self):
        adapter = _ConcreteAsyncSourceAdapter()

        result = _run(adapter.get_source_data_count(integration=MagicMock()))

        self.assertIsNone(result)

    def test_get_iterator_stub_returns_none(self):
        adapter = _ConcreteAsyncSourceAdapter()

        result = _run(
            adapter.get_iterator(integration=MagicMock(), limit=10)
        )

        self.assertIsNone(result)

    def test_get_source_data_with_paging_stub_returns_none(self):
        adapter = _ConcreteAsyncSourceAdapter()

        result = _run(
            adapter.get_source_data_with_paging(
                integration=MagicMock(), start=0, end=5
            )
        )

        self.assertIsNone(result)


class AsyncTargetAdapterAbstractStubsReturnNone(TestCase):
    def test_clear_data_stub_returns_none(self):
        adapter = _ConcreteAsyncTargetAdapter()

        result = _run(adapter.clear_data(integration=MagicMock()))

        self.assertIsNone(result)

    def test_write_data_stub_returns_none(self):
        adapter = _ConcreteAsyncTargetAdapter()

        result = _run(
            adapter.write_data(integration=MagicMock(), source_data=[1, 2])
        )

        self.assertIsNone(result)

    def test_do_target_operation_stub_returns_none(self):
        adapter = _ConcreteAsyncTargetAdapter()

        result = _run(adapter.do_target_operation(integration=MagicMock()))

        self.assertIsNone(result)
