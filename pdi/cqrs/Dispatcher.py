from typing import Type, TypeVar

from injector import inject

from IocManager import IocManager
from infrastructure.cqrs.CommandQueryBase import CommandQueryBase
from infrastructure.cqrs.ICommand import ICommand
from infrastructure.cqrs.ICommandHandler import ICommandHandler
from infrastructure.cqrs.IQuery import IQuery
from infrastructure.cqrs.IQueryHandler import IQueryHandler
from infrastructure.dependency.scopes import IScoped

T = TypeVar('T', covariant=True)


class Dispatcher(IScoped):
    @inject
    def __init__(self):
        pass

    def find_handler(self, type, handler_type: Type[T]) -> T:
        for handler_class in handler_type.__subclasses__():
            result = handler_type[type] == handler_class.__orig_bases__[0]
            if result:
                instance = IocManager.injector.get(handler_class)
                return instance

    def dispatch(self, cq: CommandQueryBase[T]) -> T:
        if isinstance(cq, IQuery):
            handler_type = IQueryHandler
        elif isinstance(cq, ICommand):
            handler_type = ICommandHandler
        else:
            raise Exception("Command or query not found")
        handler = self.find_handler(cq.__class__, handler_type)
        if handler is None:
            raise Exception("Handler not founded")
        return handler.handle(cq)
