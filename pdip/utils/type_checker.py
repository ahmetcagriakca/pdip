import builtins
import inspect
import typing
from abc import ABC


class ITypeChecker(ABC):
    def is_class(self, obj):
        if inspect.isclass(obj) and not self.is_primitive(obj):
            return True
        return False

    def is_primitive(self, obj):
        builtins_list = list(
            filter(lambda x: not x.startswith('_'), dir(builtins)))

        return hasattr(obj, '__name__') and obj.__name__ in builtins_list

    def is_generic(self, class_type):
        pass

    def is_base_generic(self, class_type):
        pass

class TypeChecker(ITypeChecker):
    def is_generic(self, class_type):
        return self._is_generic(class_type)

    def is_base_generic(self, class_type):
        return self._is_base_generic(class_type)

    def _is_generic(self, cls):
        if isinstance(cls, typing._GenericAlias):
            return True
        if isinstance(cls, typing._SpecialForm):
            return cls not in {typing.Any}
        return False

    def _is_base_generic(self, class_type):
        if isinstance(class_type, typing._GenericAlias):
            if class_type.__origin__ in {typing.Generic, typing._Protocol}:
                return False
            if isinstance(class_type, typing._VariadicGenericAlias):
                return True
            return len(class_type.__parameters__) > 0
        if isinstance(class_type, typing._SpecialForm):
            return class_type._name in {'ClassVar', 'Union', 'Optional'}
        return False
