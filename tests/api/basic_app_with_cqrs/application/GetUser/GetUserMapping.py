from tests.api.basic_app_with_cqrs.application.GetUser.GetUserDto import GetUserDto
from tests.api.basic_app_with_cqrs.domain.User import User


class GetUserMapping:
    @classmethod
    def to_dto(cls, entity: User) -> GetUserDto:
        dto = GetUserDto()
        dto.Id = entity.Id
        dto.Name = entity.Name
        dto.Surname = entity.Surname
        return dto