from pdip.cqrs.decorators import requestclass


@requestclass
class CreateNoteRequest:
    Title: str = None
    Body: str = None
