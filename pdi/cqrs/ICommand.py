from typing import Generic, TypeVar

from infrastructure.cqrs.CommandQueryBase import CommandQueryBase

C = TypeVar('C', covariant=True)


class ICommand(Generic[C], CommandQueryBase[C]):
    def __init__(self) -> C:
        pass


