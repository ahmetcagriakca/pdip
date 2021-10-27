import json
from datetime import datetime

from .date_time_encoder import DateTimeEncoder
from ..utils import TypeChecker


class BaseConverter(object):
    def __init__(self, cls=None):
        self.mappings = {}
        self.type_checker = TypeChecker()
        if cls is not None:
            self.register(cls)

    def class_mapper(self, d):
        for keys, cls in self.mappings.items():
            if keys.issuperset(d.keys()):  # are all required arguments present?
                return cls(**d)
        else:
            # Raise exception instead of silently returning None
            raise ValueError(f'Unable to find a matching class for object: {d}')

    def register(self, cls):
        instance = cls()
        mapping_data = frozenset(tuple([attr for attr, val in instance.__dict__.items()]))
        self.mappings[mapping_data] = cls
        annotations = self.get_annotations(instance)
        self.register_subclasses(annotations)
        return cls

    def ToJSON(self, obj):
        return json.dumps(dict(obj), cls=DateTimeEncoder, indent=4)

    def FromJSON(self, json_str):
        return json.loads(json_str, object_hook=self.class_mapper)

    def get_annotations(self,obj):
        if hasattr(obj, '__annotations__'):
            annotations = obj.__annotations__
            return annotations

    def register_subclasses(self, annotations):
        if annotations is not None and len(annotations) > 0:
            for key in annotations:
                value = annotations[key]
                if value == int:
                    pass
                elif value == str:
                    pass
                elif value == bool:
                    pass
                elif value == datetime:
                    pass
                elif value == float:
                    pass
                else:
                    if self.type_checker.is_generic(value):

                        if self.type_checker.is_primitive(value.__args__[0]):
                            pass
                        else:
                            self.register(value.__args__[0])
                            instance = value.__args__[0]()
                            nested_annotations = self.get_annotations(instance)
                            if nested_annotations is not None:
                                self.register_subclasses(nested_annotations)
                    elif self.type_checker.is_base_generic(value):
                        # TODO:Base generic class
                        print('value type should be a structure of', value.__args__[0])
                    elif self.type_checker.is_class(value):
                        self.register(value)
                        instance = value()
                        nested_annotations = self.get_annotations(instance)
                        if nested_annotations is not None:
                            self.register_subclasses(nested_annotations)
                    else:
                        print('Type not know', value)
