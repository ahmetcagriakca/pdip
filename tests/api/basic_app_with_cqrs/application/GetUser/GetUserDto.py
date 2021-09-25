from pdi.cqrs.decorators.dtoclass import dtoclass


@dtoclass
class GetUserDto:
    Id: int = None
    Name: str = None
    Surname: str = None
