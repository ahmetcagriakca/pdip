from pdip.cqrs.decorators import requestclass


@requestclass
class GetUserRequest:
    Name: str = None
