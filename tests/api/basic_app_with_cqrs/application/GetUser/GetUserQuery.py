from dataclasses import dataclass

from pdi.cqrs.IQuery import IQuery
from tests.api.basic_app_with_cqrs.application.GetUser.GetUserRequest import GetUserRequest
from tests.api.basic_app_with_cqrs.application.GetUser.GetUserResponse import GetUserResponse


@dataclass
class GetUserQuery(IQuery[GetUserResponse]):
    request: GetUserRequest = None
