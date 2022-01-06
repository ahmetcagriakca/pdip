import importlib
from typing import Type, TypeVar

from injector import inject

from .command_query_base import CommandQueryBase
from .icommand import ICommand
from .icommand_handler import ICommandHandler
from .iquery import IQuery
from .iquery_handler import IQueryHandler
from ..data.repository import RepositoryProvider
from ..dependency import IScoped
from ..dependency.provider import ServiceProvider
from ..exceptions import OperationalException
from ..logging.loggers.sql import SqlLogger

T = TypeVar('T', covariant=True)


class Dispatcher(IScoped):
    @inject
    def __init__(self, service_provider: ServiceProvider):
        self.service_provider = service_provider

    def find_handler(self, cq, handler_type: Type[T]) -> T:
        try:
            importlib.import_module(cq.__module__ + 'Handler')
        except Exception as ex:
            pass
        subclasses = handler_type.__subclasses__()
        for handler_class in subclasses:
            result = handler_type[cq.__class__] == handler_class.__orig_bases__[0]
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
        handler = self.find_handler(cq, handler_type)
        if handler is None:
            raise Exception("Handler not founded")
        try:
            result = handler.handle(cq)
            self.service_provider.get(RepositoryProvider).commit()
            if isinstance(cq, IQuery):
                return result
        except Exception as ex:
            self.service_provider.get(RepositoryProvider).rollback()
            self.service_provider.get(SqlLogger).exception(ex, str(ex))
            raise
        finally:
            self.service_provider.get(RepositoryProvider).close()
