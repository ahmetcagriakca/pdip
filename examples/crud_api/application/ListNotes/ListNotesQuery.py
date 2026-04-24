from dataclasses import dataclass

from pdip.cqrs import IQuery

from examples.crud_api.application.ListNotes.ListNotesRequest import ListNotesRequest
from examples.crud_api.application.ListNotes.ListNotesResponse import ListNotesResponse


@dataclass
class ListNotesQuery(IQuery[ListNotesResponse]):
    request: ListNotesRequest = None
