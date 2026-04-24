"""Unit tests for the DTO decorators under ``pdip.cqrs.decorators``.

``@dtoclass`` composes ``@dataclass`` with ``cls_to_dict`` and
``JsonConvert.register`` (see ADR-0013). These tests pin down the
contract that consumers rely on:

- Decorated classes are dataclasses with auto-generated ``__init__``.
- Instances expose ``to_dict`` that returns a shallow-dictable view
  of the instance.
- Nested decorated instances are dict-ified recursively, including
  through lists.
- The decorated class is registered with ``JsonConvert`` so the
  dispatcher can reconstruct it from a dict (the hydration side of
  the JSON pipeline).
"""

from unittest import TestCase

from pdip.cqrs.decorators import dtoclass
from pdip.json.base.json_convert import JsonConvert


@dtoclass
class Point:
    x: int = 0
    y: int = 0


@dtoclass
class Polygon:
    name: str = ""
    points: list = None


class DtoclassProducesADataclass(TestCase):
    def test_default_constructor_accepts_kwargs(self):
        point = Point(x=1, y=2)
        self.assertEqual(point.x, 1)
        self.assertEqual(point.y, 2)

    def test_defaults_are_applied_when_kwargs_omitted(self):
        self.assertEqual(Point(), Point(x=0, y=0))

    def test_equality_is_by_value(self):
        self.assertEqual(Point(1, 2), Point(1, 2))
        self.assertNotEqual(Point(1, 2), Point(3, 4))


class DtoclassAttachesToDict(TestCase):
    def test_to_dict_returns_flat_attributes(self):
        self.assertEqual(Point(1, 2).to_dict(), {"x": 1, "y": 2})

    def test_nested_dtos_inside_lists_are_converted(self):
        polygon = Polygon(name="triangle", points=[Point(0, 0), Point(1, 0), Point(0, 1)])
        result = polygon.to_dict()
        self.assertEqual(result["name"], "triangle")
        self.assertEqual(result["points"][0], {"x": 0, "y": 0})
        self.assertEqual(result["points"][2], {"x": 0, "y": 1})


class DtoclassRegistersWithJsonConvert(TestCase):
    """``@dtoclass`` calls ``JsonConvert.register`` so the class can
    be revived from a dict by the dispatcher. Test the hydration side
    via ``class_mapper``."""

    def test_class_mapper_reconstructs_the_instance_from_a_dict(self):
        revived = JsonConvert.class_mapper({"x": 3, "y": 4})
        self.assertEqual(revived, Point(x=3, y=4))
