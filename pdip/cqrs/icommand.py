from typing import Generic, TypeVar

from .command_query_base import CommandQueryBase

C = TypeVar('C', covariant=True)


class ICommand(Generic[C], CommandQueryBase[C]):
    def __init__(self) -> C:
        pass
