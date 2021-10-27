import copy

from ...utils.type_checker import TypeChecker


def cls_to_dict(cls):
    def to_dict(self):
        _dict = copy.deepcopy(self.__dict__)
        for attr_name in self.__dict__:
            attr = getattr(self, attr_name)
            if not callable(attr):
                if isinstance(attr, list):
                    entities = []
                    for entity in attr:
                        if (hasattr(entity, 'to_dict')):
                            entities.append(entity.to_dict())
                    _dict[attr_name] = entities
                elif TypeChecker().is_class(attr.__class__) and hasattr(attr, 'to_dict'):
                    _dict[attr_name] = attr.to_dict()
        return _dict

    has_attr = hasattr(cls, 'to_dict')
    if not has_attr:
        setattr(cls, 'to_dict', to_dict)
    return cls
