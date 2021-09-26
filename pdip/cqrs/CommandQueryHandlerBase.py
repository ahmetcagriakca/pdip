from typing import Generic, TypeVar, Union

from .IQuery import IQuery
from .ICommand import ICommand

CQH = TypeVar('CQH', covariant=True, bound=Union[IQuery, ICommand])


class CommandQueryHandlerBase(Generic[CQH]):
    def __init__(self) -> CQH:
        pass

    def handle(self, query: CQH) -> any:
        pass