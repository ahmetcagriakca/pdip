from injector import inject

from pdi.cqrs.Dispatcher import Dispatcher
from pdi.cqrs.ICommandHandler import ICommandHandler
from pdi.data import RepositoryProvider
from tests.api.basic_app_with_cqrs.application.CreateUser.CreateUserCommand import CreateUserCommand
from tests.api.basic_app_with_cqrs.domain.User import User


class CreateUserCommandHandler(ICommandHandler[CreateUserCommand]):
    @inject
    def __init__(self,
                 dispatcher: Dispatcher,
                 repository_provider: RepositoryProvider,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository_provider = repository_provider
        self.dispatcher = dispatcher

    def handle(self, command: CreateUserCommand):
        user = User(Name=command.request.Name, Surname=command.request.Surname)
        self.repository_provider.get(User).insert(user)
        self.repository_provider.commit()
