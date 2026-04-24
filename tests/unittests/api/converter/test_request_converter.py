"""Unit tests for ``pdip.api.converter.request_converter.RequestConverter``.

The converter maps JSON payloads to class instances by matching the
JSON keys against a registered class's constructor arguments. These
tests pin the happy path, the nested-class / list / enum registration
branches, and the unmapped-payload negative path.
"""

import enum
import json
from datetime import datetime
from typing import List
from unittest import TestCase

from pdip.api.converter.request_converter import RequestConverter


class _Leaf:
    def __init__(self, value: int = 0):
        self.value: int = value

    def __iter__(self):
        yield "value", self.value


class _WithList:
    items: List[_Leaf]

    def __init__(self, name: str = "", items=None):
        self.name: str = name
        self.items = items or []


class _Primitives:
    s: str
    i: int
    b: bool
    d: datetime
    f: float

    def __init__(self, s="", i=0, b=False, d=None, f=0.0):
        self.s = s
        self.i = i
        self.b = b
        self.d = d
        self.f = f


class _Colour(enum.Enum):
    RED = "red"
    BLUE = "blue"


class _HasEnum:
    colour: _Colour

    def __init__(self, colour=None):
        self.colour = colour


class _HasPrimitiveList:
    tags: List[int]

    def __init__(self, tags=None):
        self.tags = tags or []


class _Nested:
    leaf: _Leaf

    def __init__(self, leaf=None):
        self.leaf = leaf


class RequestConverterRegistersClasses(TestCase):
    def test_register_stores_frozenset_of_attr_names(self):
        rc = RequestConverter()

        rc.register(_Leaf)

        self.assertIn(frozenset({"value"}), rc.mappings)
        self.assertIs(rc.mappings[frozenset({"value"})], _Leaf)

    def test_register_walks_typed_list_annotation_for_subclasses(self):
        rc = RequestConverter(_WithList)

        # Both the outer class and the nested element class get
        # registered.
        self.assertIs(rc.mappings[frozenset({"name", "items"})], _WithList)
        self.assertIs(rc.mappings[frozenset({"value"})], _Leaf)

    def test_register_handles_primitive_only_annotations(self):
        rc = RequestConverter(_Primitives)

        # Only the outer class registers — primitives do not recurse.
        self.assertEqual(len(rc.mappings), 1)
        self.assertIn(
            frozenset({"s", "i", "b", "d", "f"}),
            rc.mappings,
        )

    def test_register_skips_enum_annotations(self):
        rc = RequestConverter(_HasEnum)

        # The enum type must not be registered as a payload class —
        # only the outer wrapper.
        self.assertEqual(len(rc.mappings), 1)
        self.assertIn(frozenset({"colour"}), rc.mappings)

    def test_register_skips_primitive_element_of_generic_list(self):
        rc = RequestConverter(_HasPrimitiveList)

        self.assertEqual(len(rc.mappings), 1)
        self.assertIn(frozenset({"tags"}), rc.mappings)

    def test_register_walks_nested_class_annotation_for_subclasses(self):
        rc = RequestConverter(_Nested)

        # Both the outer and the plain-class annotation (_Leaf)
        # register — the non-generic class branch.
        self.assertIs(rc.mappings[frozenset({"leaf"})], _Nested)
        self.assertIs(rc.mappings[frozenset({"value"})], _Leaf)


class RequestConverterMapsJsonPayloads(TestCase):
    def test_from_json_returns_instance_of_registered_class(self):
        rc = RequestConverter(_Leaf)

        result = rc.FromJSON('{"value": 42}')

        self.assertIsInstance(result, _Leaf)
        self.assertEqual(result.value, 42)

    def test_from_json_maps_nested_list_of_registered_children(self):
        rc = RequestConverter(_WithList)

        payload = '{"name": "batch", "items": [{"value": 1}, {"value": 2}]}'
        result = rc.FromJSON(payload)

        self.assertIsInstance(result, _WithList)
        self.assertEqual(result.name, "batch")
        self.assertEqual([item.value for item in result.items], [1, 2])

    def test_from_json_raises_value_error_for_unmapped_payload(self):
        rc = RequestConverter(_Leaf)

        with self.assertRaises(ValueError) as ctx:
            rc.FromJSON('{"unknown_field": "oops"}')

        # The exception message mentions the payload to aid debugging.
        self.assertIn("unknown_field", str(ctx.exception))

    def test_class_mapper_returns_matching_class_when_keys_are_superset(self):
        rc = RequestConverter(_Leaf)

        # ``class_mapper`` matches even when ``d`` is a strict subset of
        # the registered frozenset — but the constructor must accept it.
        result = rc.class_mapper({"value": 9})

        self.assertIsInstance(result, _Leaf)
        self.assertEqual(result.value, 9)


class RequestConverterToJson(TestCase):
    def test_to_json_serialises_iterable_object(self):
        rc = RequestConverter()

        payload = rc.ToJSON(_Leaf(value=5))

        self.assertEqual(json.loads(payload), {"value": 5})


class RequestConverterGetAnnotations(TestCase):
    def test_returns_class_annotations_dict_when_present(self):
        result = RequestConverter.get_annotations(_WithList)

        self.assertIn("items", result)
        self.assertEqual(result["items"], List[_Leaf])

    def test_returns_none_when_class_has_no_annotations(self):
        class _Bare:
            pass

        result = RequestConverter.get_annotations(_Bare())

        self.assertIsNone(result)

    def test_accepts_instance_and_reads_class_annotations(self):
        # Python 3.14 drops ``__annotations__`` from instance lookup;
        # the helper must still return the class-level dict when given
        # an instance.
        result = RequestConverter.get_annotations(_WithList(name="x", items=[]))

        self.assertIn("items", result)
