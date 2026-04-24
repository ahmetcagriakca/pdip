from pdip.cqrs.decorators import requestclass


@requestclass
class ListNotesRequest:
    # No query parameters today. Kept as a distinct type so adding
    # (e.g.) ``Search: str`` later is additive, not API-breaking.
    pass
