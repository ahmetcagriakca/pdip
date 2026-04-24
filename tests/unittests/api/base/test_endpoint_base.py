"""Unit tests for ``pdip.api.base.endpoint_base.Endpoint``.

``Endpoint`` wraps a controller method and translates its annotation
signature into flask_restx inputs / outputs. The ``basic_app*`` suites
cover the happy path via ``Pdi()``; these tests pin down the
branches those suites don't reach.
"""

from unittest import TestCase
from unittest.mock import MagicMock

from flask import Flask
from flask_restx import Api

from pdip.api.base.endpoint_base import Endpoint
from pdip.api.base.endpoint_wrapper import EndpointWrapper


def _wrapper():
    app = Flask(__name__)
    api = Api(app)
    return EndpointWrapper(api=api)


class EndpointCallInvokesFunctionWithoutRequestWhenNoInputs(TestCase):
    def test_no_annotated_inputs_calls_function_with_only_self(self):
        # Arrange — a function with zero (or only ``return``) annotated
        # inputs lands in ``find_input_type -> (None, None)`` and the
        # ``else`` branch on line 29 which skips the request argument.
        def get(self) -> dict:
            return {"ok": True}

        endpoint = Endpoint(
            function=get,
            namespace=MagicMock(),
            endpoint_wrapper=_wrapper(),
        )
        controller_self = object()

        # Act
        response = endpoint(controller_self)

        # Assert — the inner function ran and its return went through
        # ``get_response``.
        self.assertEqual(response, {"Result": {"ok": True}, "Message": None})


class EndpointCallReturnsRawWhenReturnTypeMissing(TestCase):
    def test_no_return_annotation_skips_to_dict_branch(self):
        # Arrange — no ``-> return`` annotation triggers the ``else``
        # branch on line 38-40.
        def get(self):
            return "plain"

        endpoint = Endpoint(
            function=get,
            namespace=MagicMock(),
            endpoint_wrapper=_wrapper(),
        )

        # Act
        response = endpoint(object())

        # Assert
        self.assertEqual(response, {"Result": "plain", "Message": None})


class EndpointFindInputTypeEdgeCases(TestCase):
    def test_no_annotations_returns_none_none(self):
        # Covers line 66: ``return None, None`` when no inputs.
        def fn(self):
            pass

        endpoint = Endpoint(
            function=fn,
            namespace=MagicMock(),
            endpoint_wrapper=_wrapper(),
        )

        self.assertEqual(endpoint.find_input_type(), (None, None))

    def test_multiple_annotations_returns_none_none(self):
        # Covers line 70: ``return None, None`` when >1 inputs.
        def fn(self, a: int, b: str):
            return None

        endpoint = Endpoint(
            function=fn,
            namespace=MagicMock(),
            endpoint_wrapper=_wrapper(),
        )

        self.assertEqual(endpoint.find_input_type(), (None, None))


class EndpointReturnTypeIsNoneWhenAbsent(TestCase):
    def test_return_type_returns_none_when_no_return_annotation(self):
        def fn(self):
            pass

        endpoint = Endpoint(
            function=fn,
            namespace=MagicMock(),
            endpoint_wrapper=_wrapper(),
        )

        self.assertIsNone(endpoint.return_type())


class EndpointMarshalWithFieldsFallsBackToBaseModel(TestCase):
    def test_no_return_annotation_uses_base_model(self):
        def fn(self):
            pass

        endpoint = Endpoint(
            function=fn,
            namespace=MagicMock(),
            endpoint_wrapper=_wrapper(),
        )

        fields = endpoint.marshal_with_fields()

        # BaseModel has these keys.
        self.assertIn("IsSuccess", fields)
        self.assertIn("Result", fields)
