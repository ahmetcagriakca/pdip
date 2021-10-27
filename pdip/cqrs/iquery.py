from typing import Generic, TypeVar

from .command_query_base import CommandQueryBase

Q = TypeVar('Q', covariant=True)


class IQuery(Generic[Q], CommandQueryBase[Q]):
    def __init__(self) -> Q:
        pass
