from typing import List

from pdip.cqrs.decorators import responseclass

from examples.crud_api.application.ListNotes.ListNoteDto import ListNoteDto


@responseclass
class ListNotesResponse:
    Data: List[ListNoteDto] = None
