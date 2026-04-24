"""Unit tests for ``pdip.data.domain.types.GUID``.

``GUID`` is a ``TypeDecorator`` that normalises UUID handling across
PostgreSQL (native ``UUID``) and everything else (``CHAR(32)`` hex).
Each branch is exercised with a ``MagicMock`` dialect so no real
database engine is needed.
"""

import uuid
from unittest import TestCase
from unittest.mock import MagicMock

from sqlalchemy import UUID as SA_UUID
from sqlalchemy.types import CHAR

from pdip.data.domain.types.GUID import GUID


class GUIDLoadDialectImplBranches(TestCase):
    def test_postgresql_dialect_descends_to_native_uuid(self):
        # Arrange
        subject = GUID()
        dialect = MagicMock(name="postgres_dialect")
        dialect.name = "postgresql"
        dialect.type_descriptor.return_value = "native-uuid-descriptor"

        # Act
        result = subject.load_dialect_impl(dialect)

        # Assert — the returned descriptor comes from the dialect and
        # the argument to ``type_descriptor`` is a ``sqlalchemy.UUID``.
        self.assertEqual(result, "native-uuid-descriptor")
        (arg,), _ = dialect.type_descriptor.call_args
        self.assertIsInstance(arg, SA_UUID)

    def test_non_postgresql_dialect_falls_back_to_char_32(self):
        # Arrange
        subject = GUID()
        dialect = MagicMock(name="sqlite_dialect")
        dialect.name = "sqlite"
        dialect.type_descriptor.return_value = "char-descriptor"

        # Act
        result = subject.load_dialect_impl(dialect)

        # Assert
        self.assertEqual(result, "char-descriptor")
        (arg,), _ = dialect.type_descriptor.call_args
        self.assertIsInstance(arg, CHAR)
        self.assertEqual(arg.length, 32)


class GUIDProcessBindParamBranches(TestCase):
    def test_none_value_is_passed_through(self):
        subject = GUID()
        dialect = MagicMock()
        dialect.name = "sqlite"

        self.assertIsNone(subject.process_bind_param(None, dialect))

    def test_postgresql_returns_stringified_value(self):
        subject = GUID()
        dialect = MagicMock()
        dialect.name = "postgresql"
        uid = uuid.UUID("12345678-1234-5678-1234-567812345678")

        result = subject.process_bind_param(uid, dialect)

        self.assertEqual(result, str(uid))

    def test_non_postgresql_string_input_is_hex_formatted(self):
        subject = GUID()
        dialect = MagicMock()
        dialect.name = "sqlite"

        result = subject.process_bind_param(
            "12345678-1234-5678-1234-567812345678", dialect
        )

        self.assertEqual(result, "12345678123456781234567812345678")

    def test_non_postgresql_uuid_input_is_hex_formatted(self):
        subject = GUID()
        dialect = MagicMock()
        dialect.name = "sqlite"
        uid = uuid.UUID("12345678-1234-5678-1234-567812345678")

        result = subject.process_bind_param(uid, dialect)

        self.assertEqual(result, "12345678123456781234567812345678")


class GUIDProcessResultValueBranches(TestCase):
    def test_none_value_returns_none(self):
        subject = GUID()

        self.assertIsNone(subject.process_result_value(None, MagicMock()))

    def test_string_value_is_parsed_to_uuid(self):
        subject = GUID()
        raw = "12345678123456781234567812345678"

        result = subject.process_result_value(raw, MagicMock())

        self.assertIsInstance(result, uuid.UUID)
        self.assertEqual(result.hex, raw)

    def test_uuid_value_is_passed_through(self):
        subject = GUID()
        uid = uuid.uuid4()

        result = subject.process_result_value(uid, MagicMock())

        self.assertIs(result, uid)
