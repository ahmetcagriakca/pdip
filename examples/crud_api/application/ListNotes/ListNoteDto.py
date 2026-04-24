from pdip.cqrs.decorators import dtoclass


@dtoclass
class ListNoteDto:
    Id: str = None
    Title: str = None
    Body: str = None
    CreateUserTime: str = None
