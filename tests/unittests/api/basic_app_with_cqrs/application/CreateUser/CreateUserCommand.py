from dataclasses import dataclass

from pdip.cqrs import ICommand
from tests.api.basic_app_with_cqrs.application.CreateUser.CreateUserRequest import CreateUserRequest


@dataclass
class CreateUserCommand(ICommand):
    request: CreateUserRequest = None
