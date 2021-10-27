from typing import Type, TypeVar

from injector import inject

from .command_query_base import CommandQueryBase
from .icommand import ICommand
from .icommand_handler import ICommandHandler
from .iquery import IQuery
from .iquery_handler import IQueryHandler
from ..dependency import IScoped
from ..dependency.provider import ServiceProvider

T = TypeVar('T', covariant=True)


class Dispatcher(IScoped):
    @inject
    def __init__(self, service_provider: ServiceProvider):
        self.service_provider = service_provider

    def find_handler(self, type, handler_type: Type[T]) -> T:
        for handler_class in handler_type.__subclasses__():
            result = handler_type[type] == handler_class.__orig_bases__[0]
            if result:
                instance = self.service_provider.get(handler_class)
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
