from pdip.cqrs.decorators.responseclass import responseclass
from tests.api.basic_app_with_cqrs.application.GetUser.GetUserDto import GetUserDto


@responseclass
class GetUserResponse:
	Data: GetUserDto = None
