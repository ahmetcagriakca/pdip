import json


class BaseConverter(object):
    mappings = {}

    @classmethod
    def class_mapper(clsself, d):
        for keys, cls in clsself.mappings.items():
            if keys.issuperset(d.keys()):  # are all required arguments present?
                return cls(**d)
        else:
            # Raise exception instead of silently returning None
            raise ValueError(f'Unable to find a matching class for object: {d}')

    @classmethod
    def complex_handler(clsself, Obj):
        if hasattr(Obj, '__dict__'):
            return Obj.__dict__
        else:
            raise TypeError('Object of type %s with value of %s is not JSON serializable' % (type(Obj), repr(Obj)))

    @classmethod
    def register(clsself, cls):
        clsself.mappings[
            frozenset(tuple([attr for attr, val in cls().__dict__.items() if not attr.startswith('_')]))] = cls
        return cls

    @classmethod
    def ToJSON(clsself, obj):
        return json.dumps(obj.__dict__, default=clsself.complex_handler, indent=4)

    @classmethod
    def FromJSON(clsself, json_str):
        return json.loads(json_str, object_hook=clsself.class_mapper)