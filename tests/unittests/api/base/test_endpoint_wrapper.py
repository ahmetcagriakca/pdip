"""Unit tests for ``EndpointWrapper``.

``EndpointWrapper`` translates Python annotations into ``flask_restx``
schemas and parsers. The ``basic_app*`` suites exercise the happy-path
surface end-to-end; these tests pin down the branches they don't
reach: the per-type paths of ``field_resolver``, the ``List[...]``
and ``List[any]`` paths of ``annotation_resolver``, the primitive
parser path of ``create_parser``, the generic / boolean branches of
``create_argument``, the ``PagingParameter`` / ``OrderByParameter``
branches of ``request_parser``, and the ``date_converter`` branches.

All Flask state stays local: each test instantiates a fresh
``Flask`` + ``Api`` so one test's model registrations cannot bleed
into another.
"""

import uuid
from datetime import datetime
from typing import List
from unittest import TestCase

from flask import Flask
from flask_restx import Api, fields, inputs

from pdip.api.base.endpoint_wrapper import EndpointWrapper, NullableString
from pdip.api.request_parameter import OrderByParameter, PagingParameter


def _build_wrapper():
    """Return an ``EndpointWrapper`` wired to a fresh ``Api`` on a
    fresh ``Flask`` app. Each test gets its own instance so model
    name collisions can't happen across tests."""
    app = Flask(__name__)
    api = Api(app)
    return EndpointWrapper(api=api), app, api


class _Nested:
    inner_int: int = 0


class _Wrapper:
    name: str = ""
    nested: _Nested = None


class _WithList:
    items: List[_Nested] = None


class _WithAnyList:
    items: List[any] = None


class _WithPrimitiveList:
    tags: List[str] = None


class _NoAnnotations:
    pass


class EndpointWrapperDateConverter(TestCase):
    def test_date_converter_returns_isoformat_for_datetime(self):
        moment = datetime(2026, 4, 24, 12, 30, 45)

        result = EndpointWrapper.date_converter(moment)

        self.assertEqual(result, moment.isoformat())

    def test_date_converter_returns_str_for_uuid(self):
        some_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")

        result = EndpointWrapper.date_converter(some_uuid)

        self.assertEqual(result, "12345678-1234-5678-1234-567812345678")

    def test_date_converter_returns_none_for_unrelated_type(self):
        # Neither ``datetime`` nor ``UUID`` — the function has no
        # explicit ``return`` and should fall through to ``None``.
        result = EndpointWrapper.date_converter(42)

        self.assertIsNone(result)


class EndpointWrapperGetResponse(TestCase):
    def test_get_response_wraps_result_and_message(self):
        payload = EndpointWrapper.get_response(result=7, message="ok")

        self.assertEqual(payload, {"Result": 7, "Message": "ok"})

    def test_get_response_defaults_are_none(self):
        self.assertEqual(
            EndpointWrapper.get_response(), {"Result": None, "Message": None}
        )


class EndpointWrapperFieldResolver(TestCase):
    def setUp(self):
        self.wrapper, _app, _api = _build_wrapper()

    def test_field_resolver_maps_int_to_integer_field(self):
        field = self.wrapper.field_resolver(int, "n")

        self.assertIsInstance(field, fields.Integer)

    def test_field_resolver_maps_str_to_nullable_string(self):
        field = self.wrapper.field_resolver(str, "s")

        self.assertIsInstance(field, NullableString)

    def test_field_resolver_maps_bool_to_boolean_field(self):
        field = self.wrapper.field_resolver(bool, "b")

        self.assertIsInstance(field, fields.Boolean)

    def test_field_resolver_maps_datetime_to_datetime_field(self):
        field = self.wrapper.field_resolver(datetime, "d")

        self.assertIsInstance(field, fields.DateTime)

    def test_field_resolver_maps_float_to_float_field(self):
        field = self.wrapper.field_resolver(float, "f")

        self.assertIsInstance(field, fields.Float)

    def test_field_resolver_maps_any_to_raw_field(self):
        field = self.wrapper.field_resolver(any, "a")

        self.assertIsInstance(field, fields.Raw)


class EndpointWrapperAnnotationResolverListBranches(TestCase):
    def setUp(self):
        self.wrapper, _app, _api = _build_wrapper()

    def test_annotation_resolver_list_of_any_becomes_list_of_raw(self):
        definition = self.wrapper.annotation_resolver(
            _WithAnyList.__annotations__
        )

        self.assertIn("items", definition)
        self.assertIsInstance(definition["items"], fields.List)

    def test_annotation_resolver_list_of_class_becomes_list_of_nested(self):
        definition = self.wrapper.annotation_resolver(
            _WithList.__annotations__
        )

        self.assertIn("items", definition)
        self.assertIsInstance(definition["items"], fields.List)

    def test_annotation_resolver_nested_class_becomes_nested_field(self):
        definition = self.wrapper.annotation_resolver(
            {"nested": _Nested}
        )

        self.assertIn("nested", definition)
        self.assertIsInstance(definition["nested"], fields.Nested)

    def test_annotation_resolver_ignores_unknown_type(self):
        # A random object that is neither primitive, generic, base
        # generic nor class lands in the ``print('Type not know'...)``
        # branch and is **not** added to the definition.
        unknown_sentinel = object()

        definition = self.wrapper.annotation_resolver(
            {"x": unknown_sentinel}
        )

        self.assertNotIn("x", definition)

    def test_annotation_resolver_skips_nested_class_without_annotations(self):
        # _NoAnnotations has no __annotations__; the nested branch
        # leaves it out of the resulting model definition.
        definition = self.wrapper.annotation_resolver(
            {"empty": _NoAnnotations}
        )

        self.assertNotIn("empty", definition)


class EndpointWrapperGetAnnotations(TestCase):
    def setUp(self):
        self.wrapper, _app, _api = _build_wrapper()

    def test_get_annotations_reads_from_instance_via_class(self):
        annotations = self.wrapper.get_annotations(_Nested())

        self.assertEqual(annotations, {"inner_int": int})

    def test_get_annotations_returns_none_for_class_without_annotations(self):
        self.assertIsNone(self.wrapper.get_annotations(_NoAnnotations()))


class EndpointWrapperCreateParser(TestCase):
    def setUp(self):
        self.wrapper, _app, _api = _build_wrapper()

    def test_create_parser_for_primitive_uses_args_location(self):
        parser = self.wrapper.create_parser(name="x", input_type=int)

        # Args are stored on parser.args; primitive goes to ``args``.
        self.assertEqual(parser.args[0].location, "args")
        self.assertEqual(parser.args[0].name, "x")

    def test_create_parser_for_class_uses_form_location(self):
        parser = self.wrapper.create_parser(name="x", input_type=_Nested)

        self.assertEqual(parser.args[0].location, "form")


class EndpointWrapperCreateArgument(TestCase):
    def setUp(self):
        self.wrapper, _app, _api = _build_wrapper()

    def test_create_argument_unwraps_generic_to_inner_type(self):
        arg = self.wrapper.create_argument(
            name="xs", type=List[int], location="args", help="help"
        )

        self.assertEqual(arg.type, int)

    def test_create_argument_maps_bool_to_inputs_boolean(self):
        arg = self.wrapper.create_argument(
            name="flag", type=bool, location="args", help="help"
        )

        self.assertIs(arg.type, inputs.boolean)


class EndpointWrapperRequestParserAddsPagingAndOrderByArgs(TestCase):
    def setUp(self):
        self.wrapper, _app, _api = _build_wrapper()

    def test_request_parser_adds_page_number_and_page_size_for_paging(self):
        parser = self.wrapper.request_parser(PagingParameter)

        names = [a.name for a in parser.args]
        self.assertIn("PageNumber", names)
        self.assertIn("PageSize", names)

    def test_request_parser_adds_order_and_order_by_for_order_by(self):
        parser = self.wrapper.request_parser(OrderByParameter)

        names = [a.name for a in parser.args]
        self.assertIn("OrderBy", names)
        self.assertIn("Order", names)


class EndpointWrapperBaseModelAndResponseModel(TestCase):
    def setUp(self):
        self.wrapper, _app, _api = _build_wrapper()

    def test_base_model_exposes_success_message_and_result_fields(self):
        model = self.wrapper.BaseModel

        self.assertIn("IsSuccess", model)
        self.assertIn("Message", model)
        self.assertIn("Result", model)

    def test_response_model_for_non_class_falls_back_to_base_model(self):
        # Passing a primitive forces the ``else`` branch which returns
        # ``self.BaseModel`` — the non-class branch of response_model.
        model = self.wrapper.response_model(int)

        self.assertIn("IsSuccess", model)
        self.assertIn("Result", model)

    def test_response_model_for_class_wraps_nested_model_under_result(self):
        model = self.wrapper.response_model(_Nested)

        self.assertIn("Result", model)
        # The Result field wraps the generated inner model as a
        # ``fields.Nested``.
        self.assertIsInstance(model["Result"], fields.Nested)


class EndpointWrapperRequestModel(TestCase):
    def setUp(self):
        self.wrapper, _app, _api = _build_wrapper()

    def test_request_model_returns_none_when_type_has_no_annotations(self):
        # ``_NoAnnotations`` instances have no ``__annotations__`` and
        # ``request_model`` must return None (no model registered).
        result = self.wrapper.request_model(_NoAnnotations)

        self.assertIsNone(result)

    def test_request_model_builds_model_for_annotated_type(self):
        model = self.wrapper.request_model(_Nested)

        self.assertIn("inner_int", model)
