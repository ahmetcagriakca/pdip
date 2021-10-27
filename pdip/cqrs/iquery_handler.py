from typing import Generic, TypeVar

from .command_query_handler_base import CommandQueryHandlerBase
from .iquery import IQuery

QH = TypeVar('QH', covariant=True, bound=IQuery)


class IQueryHandler(Generic[QH], CommandQueryHandlerBase[QH]):
    def __init__(self) -> QH:
        pass

    def handle(self, query: QH) -> any:
        pass
