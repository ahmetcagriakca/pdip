from injector import inject

from pdip.api.base import ResourceBase
from pdip.cqrs import Dispatcher

from examples.crud_api.application.CreateNote.CreateNoteCommand import (
    CreateNoteCommand,
)
from examples.crud_api.application.CreateNote.CreateNoteRequest import (
    CreateNoteRequest,
)
from examples.crud_api.application.ListNotes.ListNotesQuery import ListNotesQuery
from examples.crud_api.application.ListNotes.ListNotesRequest import ListNotesRequest
from examples.crud_api.application.ListNotes.ListNotesResponse import ListNotesResponse


class NotesResource(ResourceBase):
    """REST endpoint auto-mounted at ``/api/Application/Notes``.

    The convention is ``/api/<first-dir-under-application>/<resource-stem>``
    — see pdip's ``endpoint_wrapper`` (ADR-0008)."""

    @inject
    def __init__(
        self,
        dispatcher: Dispatcher,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.dispatcher = dispatcher

    def get(self, req: ListNotesRequest) -> ListNotesResponse:
        return self.dispatcher.dispatch(ListNotesQuery(request=req))

    def post(self, req: CreateNoteRequest):
        self.dispatcher.dispatch(CreateNoteCommand(request=req))
