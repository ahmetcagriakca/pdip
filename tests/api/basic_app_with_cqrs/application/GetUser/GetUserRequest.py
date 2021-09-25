from pdi.cqrs.decorators.requestclass import requestclass


@requestclass
class GetUserRequest:
    Name: str = None
