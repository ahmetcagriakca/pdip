from dataclasses import dataclass

from .cls_to_dict import cls_to_dict
from ...json.json_convert import JsonConvert


def requestclass(_cls=None):
    def wrap(cls):
        return (JsonConvert.register)(cls_to_dict(cls=(dataclass)(cls)))

    return wrap(_cls)
