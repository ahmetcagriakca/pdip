"""Unit tests for ``pdip.integrator.connection.domain.authentication.type``.

``AuthenticationTypes`` is exchanged as a plain integer in persisted
connection configuration. Pin the contract values so a member rename
cannot accidentally renumber and break the on-disk schema.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402

from pdip.integrator.connection.domain.authentication.type import (  # noqa: E402
    AuthenticationTypes,
)
from pdip.integrator.connection.domain.authentication.type.authentication_types import (  # noqa: E402
    AuthenticationTypes as AuthenticationTypesDirect,
)


class AuthenticationTypesMembersPinContractValues(TestCase):
    def test_no_authentication_member_has_value_zero(self):
        self.assertEqual(AuthenticationTypes.NoAuthentication.value, 0)

    def test_basic_authentication_member_has_value_one(self):
        self.assertEqual(AuthenticationTypes.BasicAuthentication.value, 1)

    def test_kerberos_member_has_value_two(self):
        self.assertEqual(AuthenticationTypes.Kerberos.value, 2)

    def test_package_reexport_is_same_enum_type(self):
        self.assertIs(AuthenticationTypes, AuthenticationTypesDirect)

    def test_enum_contains_exactly_three_members(self):
        self.assertEqual(
            sorted(m.name for m in AuthenticationTypes),
            ["BasicAuthentication", "Kerberos", "NoAuthentication"],
        )
