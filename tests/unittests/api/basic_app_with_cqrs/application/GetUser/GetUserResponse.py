from pdip.cqrs.decorators import responseclass
from tests.unittests.api.basic_app_with_cqrs.application.GetUser.GetUserDto import GetUserDto


@responseclass
class GetUserResponse:
    Data: GetUserDto = None
