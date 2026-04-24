"""Unit tests for the abstract ``pdip.cqrs.generator.domain.generator.Generator``.

``Generator`` is a single-method ABC whose ``generate`` body is
``pass``. Exercise the stub through a concrete subclass to pin the
base signature.
"""

from unittest import TestCase
from unittest.mock import MagicMock

from pdip.cqrs.generator.domain.generator import Generator


class _ConcreteGenerator(Generator):
    def generate(self, generate_config):
        return super().generate(generate_config)


class GeneratorBaseStub(TestCase):
    def test_super_generate_returns_none(self):
        subject = _ConcreteGenerator()

        result = subject.generate(generate_config=MagicMock())

        self.assertIsNone(result)
