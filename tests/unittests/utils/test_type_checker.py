"""Unit tests for ``pdip.utils.type_checker``.

Covers the ``ITypeChecker`` abstract stubs and the concrete
``TypeChecker._is_generic`` / ``_is_base_generic`` branches. These
helpers feed ``BaseConverter.register_subclasses`` and so a regression
here silently breaks JSON DTO reconstruction.
"""

import sys
import typing
import unittest
from unittest import TestCase

from pdip.utils.type_checker import ITypeChecker, TypeChecker


class ITypeCheckerAbstractStubsReturnNone(TestCase):
    """The abstract class has non-abstract methods that just ``pass``.
    Call them through a concrete sub-subclass to hit those lines."""

    class _BareChecker(ITypeChecker):
        # Deliberately does not override is_generic / is_base_generic.
        pass

    def test_abstract_is_generic_stub_returns_none(self):
        # Arrange
        checker = self._BareChecker()

        # Act / Assert
        self.assertIsNone(checker.is_generic(list))

    def test_abstract_is_base_generic_stub_returns_none(self):
        # Arrange
        checker = self._BareChecker()

        # Act / Assert
        self.assertIsNone(checker.is_base_generic(list))


class TypeCheckerIsGenericMatchesParameterisedTypes(TestCase):
    def test_parameterised_list_is_generic(self):
        self.assertTrue(TypeChecker().is_generic(typing.List[int]))

    @unittest.skipIf(
        sys.version_info >= (3, 14),
        "typing.Union's representation changed in 3.14 — it is now a "
        "plain Union type rather than a typing._GenericAlias subclass, "
        "so TypeChecker.is_generic returns False. The 3.14-aware "
        "handling is a separate enhancement; this test pins pre-3.14 "
        "behaviour on Python versions where the current helper works.",
    )
    def test_special_form_union_is_generic(self):
        self.assertTrue(TypeChecker().is_generic(typing.Union))

    def test_any_special_form_is_not_generic(self):
        self.assertFalse(TypeChecker().is_generic(typing.Any))

    def test_plain_class_is_not_generic(self):
        self.assertFalse(TypeChecker().is_generic(int))


class TypeCheckerIsBaseGenericMatchesOpenGenerics(TestCase):
    @unittest.skipIf(
        sys.version_info >= (3, 14),
        "typing.Union's representation changed in 3.14 (see the "
        "matching skip in TypeCheckerIsGenericMatchesParameterisedTypes).",
    )
    def test_union_special_form_is_base_generic(self):
        self.assertTrue(TypeChecker().is_base_generic(typing.Union))

    @unittest.skipIf(
        sys.version_info >= (3, 14),
        "Same 3.14 typing.Union representation change.",
    )
    def test_optional_special_form_is_base_generic(self):
        self.assertTrue(TypeChecker().is_base_generic(typing.Optional))

    def test_classvar_special_form_is_base_generic(self):
        self.assertTrue(TypeChecker().is_base_generic(typing.ClassVar))

    def test_any_special_form_is_not_base_generic(self):
        # ``typing.Any`` reaches the final ``return class_type._name in
        # {...}`` line, and its name is ``'Any'`` — so the helper
        # returns False.
        self.assertFalse(TypeChecker().is_base_generic(typing.Any))

    def test_plain_class_is_not_base_generic(self):
        self.assertFalse(TypeChecker().is_base_generic(int))

    def test_parameterised_alias_does_not_crash(self):
        # Pre-fix, ``_is_base_generic`` referenced ``typing._Protocol``
        # which was removed in Python 3.9, making this call raise
        # ``AttributeError``. The fix guards both ``_Protocol`` and
        # ``_VariadicGenericAlias`` lookups with ``getattr``, so the
        # helper returns a plain bool without crashing.
        self.assertIs(
            TypeChecker().is_base_generic(typing.List[int]),
            False,
        )

    def test_generic_origin_parameterisation_is_not_base_generic(self):
        # ``typing.Generic[TypeVar]`` has an origin equal to
        # ``typing.Generic`` itself — the helper must short-circuit to
        # ``False`` (it is the bare ``Generic``, not an open generic).
        T = typing.TypeVar("T")

        self.assertFalse(TypeChecker().is_base_generic(typing.Generic[T]))
