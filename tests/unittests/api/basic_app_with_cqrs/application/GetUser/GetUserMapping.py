from tests.unittests.api.basic_app_with_cqrs.application.GetUser.GetUserDto import GetUserDto
from tests.unittests.api.basic_app_with_cqrs.domain.user.User import User


class GetUserMapping:
    @classmethod
    def to_dto(cls, entity: User) -> GetUserDto:
        dto = GetUserDto()
        dto.Id = entity.Id
        dto.Name = entity.Name
        dto.Surname = entity.Surname
        return dto
