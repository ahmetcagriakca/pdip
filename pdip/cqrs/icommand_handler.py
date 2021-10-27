from typing import Generic, TypeVar

from .command_query_handler_base import CommandQueryHandlerBase
from .icommand import ICommand

CH = TypeVar('CH', covariant=True, bound=ICommand)


class ICommandHandler(Generic[CH], CommandQueryHandlerBase[CH]):
    def __init__(self) -> CH:
        pass

    def handle(self, query: CH) -> CH:
        pass
