from typing import Generic, TypeVar

from .iquery import IQuery
from .command_query_handler_base import CommandQueryHandlerBase

QH = TypeVar('QH', covariant=True, bound=IQuery)


class IQueryHandler(Generic[QH], CommandQueryHandlerBase[QH]):
    def __init__(self) -> QH:
        pass

    def handle(self, query: QH) -> any:
        pass