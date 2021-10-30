from dataclasses import dataclass

from pdip.cqrs import IQuery
from tests.unittests.api.basic_app_with_cqrs.application.GetUser.GetUserRequest import GetUserRequest
from tests.unittests.api.basic_app_with_cqrs.application.GetUser.GetUserResponse import GetUserResponse


@dataclass
class GetUserQuery(IQuery[GetUserResponse]):
    request: GetUserRequest = None
