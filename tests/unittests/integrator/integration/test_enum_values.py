"""Unit tests for ``pdip.integrator.integration.domain.enums``.

``IntegrationTypes`` is a flat ``Enum`` whose integer values are
exchanged on the wire (they appear in persisted operation / integration
records). Pin the numeric contract so a rename does not silently
renumber and corrupt downstream consumers.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402

from pdip.integrator.integration.domain.enums import IntegrationTypes  # noqa: E402
from pdip.integrator.integration.domain.enums.integration_types import (  # noqa: E402
    IntegrationTypes as IntegrationTypesDirect,
)


class IntegrationTypesMembersPinContractValues(TestCase):
    def test_source_member_has_value_one(self):
        self.assertEqual(IntegrationTypes.Source.value, 1)

    def test_target_member_has_value_two(self):
        self.assertEqual(IntegrationTypes.Target.value, 2)

    def test_source_to_target_member_has_value_three(self):
        self.assertEqual(IntegrationTypes.SourceToTarget.value, 3)

    def test_package_reexport_is_same_enum_type(self):
        # The package __init__ re-exports the enum; guard against an
        # accidental divergence between the two import paths.
        self.assertIs(IntegrationTypes, IntegrationTypesDirect)

    def test_enum_contains_exactly_three_members(self):
        self.assertEqual(
            sorted(m.name for m in IntegrationTypes),
            ["Source", "SourceToTarget", "Target"],
        )
