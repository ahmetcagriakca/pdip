"""Unit tests for ``pdip.json.base.base_converter.BaseConverter``.

``BaseConverter`` is the reflective engine behind ``JsonConvert``: it
walks annotations, registers nested dataclass-style containers, and
converts Row/dict/object shapes to JSON. These tests nail down its
branch behaviour so regressions land here, not in downstream DTO flows.
"""

import json
import uuid
from typing import List
from unittest import TestCase
from unittest.mock import MagicMock

from sqlalchemy import Row

from pdip.json.base.base_converter import BaseConverter


class _Leaf:
    name: str = ""

    def __init__(self, name: str = ""):
        self.name = name

    def __iter__(self):
        yield from self.__dict__.items()

    def __eq__(self, other):
        return isinstance(other, _Leaf) and self.__dict__ == other.__dict__


class _Container:
    count: int = 0
    label: str = ""
    flag: bool = False
    ratio: float = 0.0
    leaf: _Leaf = None

    def __init__(self, count: int = 0, label: str = "",
                 flag: bool = False, ratio: float = 0.0,
                 leaf: _Leaf = None):
        self.count = count
        self.label = label
        self.flag = flag
        self.ratio = ratio
        self.leaf = leaf if leaf is not None else _Leaf()

    def __iter__(self):
        yield from self.__dict__.items()


class _WithGenericPrimitive:
    tags: List[str] = None

    def __init__(self, tags=None):
        self.tags = tags if tags is not None else []


class _GenericLeaf:
    value: int = 0

    def __init__(self, value=0):
        self.value = value


class _WithGenericClass:
    leaves: List[_GenericLeaf] = None

    def __init__(self, leaves=None):
        self.leaves = leaves if leaves is not None else []


class BaseConverterRegistersClass(TestCase):
    def test_constructor_registers_class_and_maps_fields(self):
        # Arrange + Act
        converter = BaseConverter(_Leaf)

        # Assert
        field_sets = list(converter.mappings.keys())
        self.assertEqual(len(field_sets), 1)
        self.assertIn("name", field_sets[0])
        self.assertIs(converter.mappings[field_sets[0]], _Leaf)

    def test_register_walks_nested_annotations_for_class_fields(self):
        # Arrange
        converter = BaseConverter()

        # Act
        converter.register(_Container)

        # Assert: both the container and the nested _Leaf get registered.
        registered_classes = set(converter.mappings.values())
        self.assertIn(_Container, registered_classes)
        self.assertIn(_Leaf, registered_classes)


class BaseConverterClassMapperMatchesShape(TestCase):
    def test_class_mapper_returns_class_instance_for_matching_keys(self):
        # Arrange
        converter = BaseConverter(_Leaf)

        # Act
        revived = converter.class_mapper({"name": "alpha"})

        # Assert
        self.assertIsInstance(revived, _Leaf)
        self.assertEqual(revived.name, "alpha")

    def test_class_mapper_raises_valueerror_when_no_mapping_matches(self):
        # Arrange
        converter = BaseConverter()

        # Act + Assert
        with self.assertRaises(ValueError) as ctx:
            converter.class_mapper({"nope": 1})
        self.assertIn("Unable to find a matching class", str(ctx.exception))


class BaseConverterToJSONHandlesRowAndObject(TestCase):
    def test_tojson_serialises_plain_dict(self):
        # Arrange
        converter = BaseConverter()

        # Act
        payload = converter.ToJSON({"a": 1})

        # Assert
        self.assertEqual(json.loads(payload), {"a": 1})

    def test_tojson_serialises_sqlalchemy_row_via_asdict(self):
        # Arrange
        converter = BaseConverter()
        row = MagicMock(spec=Row)
        row._asdict.return_value = {"id": 7, "name": "row"}

        # Act
        payload = converter.ToJSON(row)

        # Assert
        self.assertEqual(json.loads(payload), {"id": 7, "name": "row"})
        row._asdict.assert_called_once()

    def test_tojson_serialises_iterable_object_via_dict(self):
        # Arrange
        converter = BaseConverter(_Leaf)
        obj = _Leaf(name="beta")

        # Act
        payload = converter.ToJSON(obj)

        # Assert
        self.assertEqual(json.loads(payload), {"name": "beta"})


class BaseConverterFromJSONUsesRegisteredMappings(TestCase):
    def test_fromjson_reconstructs_registered_class(self):
        # Arrange
        converter = BaseConverter(_Leaf)

        # Act
        revived = converter.FromJSON('{"name": "gamma"}')

        # Assert
        self.assertIsInstance(revived, _Leaf)
        self.assertEqual(revived.name, "gamma")


class BaseConverterCheckUUIDHandlesRowOfUuids(TestCase):
    def test_check_uuid_passes_non_row_through_unchanged(self):
        # Arrange
        converter = BaseConverter()
        payload = {"id": uuid.uuid4()}

        # Act
        result = converter.check_uuid(payload)

        # Assert
        self.assertIs(result, payload)

    def test_check_uuid_stringifies_uuid_entries_in_row(self):
        # Arrange
        converter = BaseConverter()
        uid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        captured = {}

        class _FakeRow(Row):
            def __init__(self):
                pass

            def __iter__(self):
                return iter([uid, "keep"])

            def __setitem__(self, idx, value):
                captured[idx] = value

        # Act
        result = converter.check_uuid(_FakeRow())

        # Assert
        self.assertEqual(captured, {0: str(uid)})
        self.assertIsInstance(result, _FakeRow)


class BaseConverterGetAnnotationsReadsClass(TestCase):
    def test_returns_none_when_class_has_no_annotations(self):
        # Arrange
        class _Empty:
            pass
        converter = BaseConverter()

        # Act
        result = converter.get_annotations(_Empty())

        # Assert
        self.assertIsNone(result)

    def test_returns_annotation_dict_when_present(self):
        # Arrange
        converter = BaseConverter()

        # Act
        annotations = converter.get_annotations(_Leaf())

        # Assert
        self.assertEqual(annotations, {"name": str})


class BaseConverterRegisterSubclassesCoversBranches(TestCase):
    def test_primitive_generic_element_is_skipped(self):
        # Arrange
        converter = BaseConverter()

        # Act
        converter.register(_WithGenericPrimitive)

        # Assert: only the container itself gets mapped; str inside
        # ``List[str]`` must not be registered.
        self.assertEqual(len(converter.mappings), 1)
        self.assertIn(_WithGenericPrimitive, converter.mappings.values())

    def test_class_inside_generic_is_registered(self):
        # Arrange
        converter = BaseConverter()

        # Act
        converter.register(_WithGenericClass)

        # Assert
        registered = set(converter.mappings.values())
        self.assertIn(_WithGenericClass, registered)
        self.assertIn(_GenericLeaf, registered)

    def test_empty_annotations_is_a_no_op(self):
        # Arrange
        converter = BaseConverter()
        before = dict(converter.mappings)

        # Act
        converter.register_subclasses(None)
        converter.register_subclasses({})

        # Assert
        self.assertEqual(converter.mappings, before)
