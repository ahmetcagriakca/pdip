import json
from datetime import datetime
import typing
from flask import request
from flask_restx import Api, fields, inputs
from flask_restx.reqparse import RequestParser, Argument
from injector import inject

from pdi.api.request_parameter.order_by_parameter import OrderByParameter
from pdi.api.request_parameter.paging_parameter import PagingParameter
from pdi.api.converter.request_converter import RequestConverter
from pdi.utils.type_checker import TypeChecker
from pdi.json.json_convert import JsonConvert

T = typing.TypeVar('T')


class NullableString(fields.String):
    __schema_type__ = ['string', 'null']
    __schema_example__ = 'nullable string'


class EndpointWrapper:
    @inject
    def __init__(self, api: Api) -> None:
        self.api = api
        self.type_checker = TypeChecker()

    @property
    def BaseModel(cls):
        return cls.api.model('BaseModel', {
            'IsSuccess': fields.Boolean(description='Is Success', default=True),
            'Message': fields.String(description='Message', default="Operation Completed"),
            'Result': fields.Raw(description='Service result values'),
        })

    @staticmethod
    def date_converter(o):
        if isinstance(o, datetime):
            return o.isoformat()

    @staticmethod
    def get_response(result=None, message=None):
        return {'Result': result, 'Message': message}

    def get_error_response(self, message):
        return {"IsSuccess": False, 'Message': message}

    def field_resolver(self, value, key):

        if value == int:
            specified_value = fields.Integer(description=f'{key}')
        elif value == str:
            specified_value = NullableString(description=f'{key}')
        elif value == bool:
            specified_value = fields.Boolean(description=f'{key}')
        elif value == datetime:
            specified_value = fields.DateTime(description=f'{key}', example=(datetime.now().isoformat()))
        elif value == float:
            specified_value = fields.Float(description=f'{key}')
        elif value == any:
            specified_value = fields.Raw(description=f'{key}')
        return specified_value

    def annotation_resolver(self, annotations):
        definition = {}
        for key in annotations:
            value = annotations[key]
            specified_value = None
            if self.type_checker.is_primitive(value):
                specified_value = self.field_resolver(value, key)
            elif self.type_checker.is_generic(value):
                if value.__args__[0] is any:
                    specified_value = fields.List(fields.Raw(), description=f'')
                else:
                    instance = value.__args__[0]()
                    nested_annotations = self.get_annotations(instance)
                    if nested_annotations is not None:
                        nested_model_definition = self.annotation_resolver(nested_annotations)
                        nested_model = self.api.model(value.__args__[0].__name__, nested_model_definition)
                        specified_value = fields.List(fields.Nested(nested_model), description=f'')
            elif self.type_checker.is_base_generic(value):
                # TODO:Base generic class
                print('value type should be a structure of', value.__args__[0])
            elif self.type_checker.isclass(value):
                instance = value()
                nested_annotations = self.get_annotations(instance)
                if nested_annotations is not None:
                    nested_model_definition = self.annotation_resolver(nested_annotations)
                    nested_model = self.api.model(value.__name__, nested_model_definition)
                    specified_value = fields.Nested(nested_model, description=f'')
            else:
                print('Type not know', value)
            if specified_value is not None:
                definition[key] = specified_value
        return definition

    def request_model(self, model_type: typing.Type[T]) -> RequestParser:
        instance = model_type()
        annotations = self.get_annotations(instance)
        if annotations is not None:
            model_definition = self.annotation_resolver(annotations)
            model = self.api.model(model_type.__name__, model_definition)
            return model

    def response_model(self, model_type: typing.Type[T]) -> RequestParser:
        if self.type_checker.is_class(model_type):
            instance = model_type()
            annotations = self.get_annotations(instance)
            if annotations is not None:
                model_definition = self.annotation_resolver(annotations)
                model = self.api.model(model_type.__name__, model_definition)
                success_model = self.api.model(model_type.__name__ + 'Base', {
                    'IsSuccess': fields.Boolean(description='Is Success', default=True),
                    'Message': fields.String(description='Message', default=None),
                    'Result': fields.Nested(model, description='Result'),
                })
                return success_model
        else:
            # success_model = self.api.model(model_type.__name__ + 'Base', {
            #     'IsSuccess': fields.Boolean(description='Is Success', default=True),
            #     'Message': fields.String(description='Message', default=None),
            #     'Result': fields.Raw(description=f'Result'),
            # })
            return self.BaseModel

    def create_parser(self, name, input_type: typing.Type[T]) -> RequestParser:
        parser: RequestParser = self.api.parser()

        if TypeChecker().is_class(input_type) == True:
            parser.add_argument(self.create_argument(name=name, type=input_type, location='form', help=name))
        else:
            parser.add_argument(self.create_argument(name=name, type=input_type, location='args', help=name))
        return parser

    def get_request_from_parser_for_primitive(self, name, input_type: typing.Type[T]) -> T:
        parser = self.create_parser(name=name, input_type=input_type)
        data = parser.parse_args(request)
        # req: T = JsonConvert.FromJSON(json.dumps(data))
        return data[name]

    def create_argument(self, name, type, location, help) -> Argument:
        specified_type = type
        if TypeChecker().is_generic(type) == True:
            specified_type = type.__args__[0]

        if specified_type == bool:
            specified_type = inputs.boolean
        argument = Argument( name, type=specified_type, location=location, help=help)
        return argument

    def get_annotations(self, obj):
        if hasattr(obj, '__annotations__'):
            annotations = obj.__annotations__
            return annotations
        else:
            return None

    def request_parser(self, parser_type: typing.Type[T]) -> RequestParser:
        parser: RequestParser = self.api.parser()
        instance = parser_type()
        if isinstance(instance, PagingParameter):
            parser.add_argument('PageNumber', type=int, location='args', help='Page Number')
            parser.add_argument('PageSize', type=int, location='args', help='Page Size')
        if isinstance(instance, OrderByParameter):
            parser.add_argument('OrderBy', type=str, location='args', help='Order By')
            parser.add_argument('Order', type=str, location='args', help='Order')
        annotations = self.get_annotations(instance)
        if annotations is not None:
            for name in annotations:
                value = annotations[name]
                parser.add_argument(self.create_argument(name=name, type=value, location='args', help=name))
        return parser

    def get_request_from_parser(self, parser_type: typing.Type[T]) -> T:
        data = self.request_parser(parser_type).parse_args(request)
        req: T = JsonConvert.FromJSON(json.dumps(data))
        return req

    def get_request_from_body(self, parser_type: typing.Type[T]) -> T:
        request_converter = RequestConverter()
        request_converter.register(parser_type)
        data = self.api.payload
        req: T = request_converter.FromJSON(json.dumps(data))
        return req
