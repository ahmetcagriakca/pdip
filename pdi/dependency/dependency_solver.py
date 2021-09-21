from typing import Type, TypeVar

from injector import Injector, inject

T = TypeVar('T')


class DependencySolver:
    @inject
    def __init__(self, injector: Injector = None) -> None:
        self.injector: Injector = injector

    def get(self, generic_type: Type[T]) -> T:
        return self.injector.get(generic_type)
