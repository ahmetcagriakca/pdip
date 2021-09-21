from dataclasses import dataclass

from infrastructure.cqrs.decorators.cls_to_dict import cls_to_dict
from infrastructure.json.JsonConvert import JsonConvert


def responseclass(_cls=None):
    def wrap(cls):
        return (JsonConvert.register)(cls_to_dict(cls=(dataclass)(cls)))

    if _cls is None:
        return wrap

    return wrap(_cls)
