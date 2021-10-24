from injector import inject

from pdip.api.base import ResourceBase
from pdip.cqrs.Dispatcher import Dispatcher
from tests.api.basic_app_with_cqrs.application.CreateUser.CreateUserCommand import CreateUserCommand
from tests.api.basic_app_with_cqrs.application.CreateUser.CreateUserRequest import CreateUserRequest
from tests.api.basic_app_with_cqrs.application.GetUser.GetUserQuery import GetUserQuery
from tests.api.basic_app_with_cqrs.application.GetUser.GetUserRequest import GetUserRequest
from tests.api.basic_app_with_cqrs.application.GetUser.GetUserResponse import GetUserResponse


class UserCqrsResource(ResourceBase):
    @inject
    def __init__(self,
                 dispatcher: Dispatcher,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dispatcher = dispatcher

    def get(self, req: GetUserRequest) -> GetUserResponse:
        query = GetUserQuery(request=req)
        res = self.dispatcher.dispatch(query)
        return res

    def post(self, req: CreateUserRequest):
        command = CreateUserCommand(request=req)
        self.dispatcher.dispatch(command)
