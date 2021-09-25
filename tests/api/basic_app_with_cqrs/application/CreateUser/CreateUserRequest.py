from pdi.cqrs.decorators.requestclass import requestclass


@requestclass
class CreateUserRequest:
    Name: str = None
    Surname: str = None
