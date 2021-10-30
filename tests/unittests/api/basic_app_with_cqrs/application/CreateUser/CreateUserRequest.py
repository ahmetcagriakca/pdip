from typing import List

from pdip.cqrs.decorators import requestclass


@requestclass
class CreateUserRequest:
    Name: str = None
    Surname: str = None
    Phones: List[str] = None
