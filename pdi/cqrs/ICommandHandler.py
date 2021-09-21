from typing import Generic, TypeVar

from infrastructure.cqrs.CommandQueryHandlerBase import CommandQueryHandlerBase
from infrastructure.cqrs.ICommand import ICommand

CH = TypeVar('CH', covariant=True, bound=ICommand)


class ICommandHandler(Generic[CH], CommandQueryHandlerBase[CH]):
    def __init__(self) -> CH:
        pass

    def handle(self, query: CH) -> CH:
        pass