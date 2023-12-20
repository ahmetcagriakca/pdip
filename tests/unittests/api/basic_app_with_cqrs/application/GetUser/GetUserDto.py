from pdip.cqrs.decorators import dtoclass


@dtoclass
class GetUserDto:
    Id: str = None
    Name: str = None
    Surname: str = None
