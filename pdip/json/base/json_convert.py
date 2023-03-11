import json

from . import DateTimeEncoder


class JsonConvert(object):
    mappings = {}

    @classmethod
    def class_mapper(clsself, d):
        dataFrozenset = frozenset(tuple([attr for attr, val in d.items()]))
        for keys, cls in clsself.mappings.items():
            if keys.issuperset(d.keys()) and dataFrozenset.issuperset(keys):  # are all required arguments present?
                return cls(**d)
        else:
            # Raise exception instead of silently returning None
            raise ValueError(f'Unable to find a matching class for object: {d}')

    @classmethod
    def register(clsself, cls):
        clsself.mappings[frozenset(tuple([attr for attr, val in cls().__dict__.items()]))] = cls
        return cls

    @classmethod
    def ToJSON(clsself, obj):
        return json.dumps(dict(obj), cls=DateTimeEncoder, indent=4)

    @classmethod
    def FromJSON(clsself, json_str):
        return json.loads(json_str, object_hook=clsself.class_mapper)
