"""Unit tests for ``InMemoryConnectionConfiguration``.

The configuration is a ``@dataclass`` with five ``None``-default
fields. The contract worth locking down is:

 * each field defaults to ``None`` when the dataclass is constructed
   with no kwargs,
 * instances with identical field values compare equal (dataclass
   ``__eq__``),
 * instances with different field values compare unequal,
 * non-default field values round-trip through the constructor.

This suite does **not** touch the ``integrator/connection/types/inmemory``
adapter package, which is out of scope per the task brief.
"""

from unittest import TestCase

from pdip.integrator.connection.domain.enums import (
    ConnectionTypes,
    ConnectorTypes,
)
from pdip.integrator.connection.domain.types.inmemory.in_memory_connection_configuration import (
    InMemoryConnectionConfiguration,
)


class InMemoryConfigurationDefaults(TestCase):
    def test_default_construction_leaves_name_none(self):
        config = InMemoryConnectionConfiguration()

        self.assertIsNone(config.Name)

    def test_default_construction_leaves_connection_string_none(self):
        config = InMemoryConnectionConfiguration()

        self.assertIsNone(config.ConnectionString)

    def test_default_construction_leaves_connection_type_none(self):
        config = InMemoryConnectionConfiguration()

        self.assertIsNone(config.ConnectionType)

    def test_default_construction_leaves_connector_type_none(self):
        config = InMemoryConnectionConfiguration()

        self.assertIsNone(config.ConnectorType)

    def test_default_construction_leaves_database_none(self):
        config = InMemoryConnectionConfiguration()

        self.assertIsNone(config.Database)


class InMemoryConfigurationRoundTripsFieldValues(TestCase):
    def test_fields_are_stored_as_passed(self):
        config = InMemoryConnectionConfiguration(
            Name="mem",
            ConnectionString="sqlite:///:memory:",
            ConnectionType=ConnectionTypes.InMemory,
            ConnectorType=ConnectorTypes.SqLite,
            Database="db",
        )

        self.assertEqual(config.Name, "mem")
        self.assertEqual(config.ConnectionString, "sqlite:///:memory:")
        self.assertIs(config.ConnectionType, ConnectionTypes.InMemory)
        self.assertIs(config.ConnectorType, ConnectorTypes.SqLite)
        self.assertEqual(config.Database, "db")


class InMemoryConfigurationEqualityContract(TestCase):
    def test_instances_with_identical_fields_compare_equal(self):
        a = InMemoryConnectionConfiguration(
            Name="mem",
            ConnectionType=ConnectionTypes.InMemory,
            ConnectorType=ConnectorTypes.SqLite,
        )
        b = InMemoryConnectionConfiguration(
            Name="mem",
            ConnectionType=ConnectionTypes.InMemory,
            ConnectorType=ConnectorTypes.SqLite,
        )

        self.assertEqual(a, b)

    def test_instances_with_different_names_compare_unequal(self):
        a = InMemoryConnectionConfiguration(Name="a")
        b = InMemoryConnectionConfiguration(Name="b")

        self.assertNotEqual(a, b)

    def test_instances_with_different_connector_types_compare_unequal(self):
        a = InMemoryConnectionConfiguration(ConnectorType=ConnectorTypes.SqLite)
        b = InMemoryConnectionConfiguration(ConnectorType=ConnectorTypes.MSSQL)

        self.assertNotEqual(a, b)
