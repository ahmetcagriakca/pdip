"""Unit tests for ``pdip.utils.type_checker``.

Covers the ``ITypeChecker`` abstract stubs and the concrete
``TypeChecker._is_generic`` / ``_is_base_generic`` branches. These
helpers feed ``BaseConverter.register_subclasses`` and so a regression
here silently breaks JSON DTO reconstruction.
"""

import typing
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

    def test_special_form_union_is_generic(self):
        # ``typing.Union`` is a SpecialForm that isn't ``Any`` — the
        # helper treats it as generic.
        self.assertTrue(TypeChecker().is_generic(typing.Union))

    def test_any_special_form_is_not_generic(self):
        self.assertFalse(TypeChecker().is_generic(typing.Any))

    def test_plain_class_is_not_generic(self):
        self.assertFalse(TypeChecker().is_generic(int))


class TypeCheckerIsBaseGenericMatchesOpenGenerics(TestCase):
    def test_union_special_form_is_base_generic(self):
        self.assertTrue(TypeChecker().is_base_generic(typing.Union))

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

    def test_parameterised_alias_crashes_on_missing_typing_private(self):
        # ``_is_base_generic`` references ``typing._Protocol`` which
        # was removed in Python 3.9. Passing any ``_GenericAlias``
        # therefore raises ``AttributeError``. This test pins the
        # current broken behaviour so whoever fixes the source also
        # updates the test.
        with self.assertRaises(AttributeError):
            TypeChecker().is_base_generic(typing.List[int])
