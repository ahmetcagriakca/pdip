"""Unit tests for the abstract ``pdip.data.seed.seed.Seed``.

``Seed`` declares a single ``@abstractmethod`` ``seed`` whose body is
``pass``. Exercise it through a concrete subclass so the stub body
executes.
"""

from unittest import TestCase

from pdip.data.seed.seed import Seed


class _ConcreteSeed(Seed):
    def seed(self):
        return super().seed()


class SeedAbstractStubReturnsNone(TestCase):
    def test_super_seed_returns_none(self):
        subject = _ConcreteSeed()

        result = subject.seed()

        self.assertIsNone(result)
