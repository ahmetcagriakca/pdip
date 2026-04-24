"""Unit tests for ``ConfigParameterBase``.

``ConfigParameterBase`` is the base entity the CQRS seed and
``ConfigService`` subclass for runtime lookups. The constructor
cooperates with ``EntityBase`` via ``super().__init__(*args, **kwargs)``
and then assigns the four config-specific attributes. These tests pin
that contract directly, without booting a database or the DI
container.
"""

from unittest import TestCase

from pdip.configuration.services.config_parameter_base import (
    ConfigParameterBase,
)


class ConfigParameterBaseStoresFields(TestCase):
    def test_defaults_all_fields_to_none(self):
        subject = ConfigParameterBase()
        self.assertIsNone(subject.Name)
        self.assertIsNone(subject.Type)
        self.assertIsNone(subject.Value)
        self.assertIsNone(subject.Description)

    def test_assigns_named_fields(self):
        subject = ConfigParameterBase(
            Name="api_key",
            Type="str",
            Value="abc",
            Description="the api key",
        )
        self.assertEqual(subject.Name, "api_key")
        self.assertEqual(subject.Type, "str")
        self.assertEqual(subject.Value, "abc")
        self.assertEqual(subject.Description, "the api key")

    def test_forwards_entity_base_kwargs_to_super(self):
        # ``EntityBase`` assigns ``Id`` via its own constructor. Make
        # sure the subclass forwards it instead of swallowing it.
        subject = ConfigParameterBase(
            Name="n", Id="id-42"
        )
        self.assertEqual(subject.Id, "id-42")
        self.assertEqual(subject.Name, "n")
