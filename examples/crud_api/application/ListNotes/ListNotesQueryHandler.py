from injector import inject

from pdip.cqrs import IQueryHandler
from pdip.data.repository import RepositoryProvider
from pdip.dependency import IScoped

from examples.crud_api.application.ListNotes.ListNoteDto import ListNoteDto
from examples.crud_api.application.ListNotes.ListNotesQuery import ListNotesQuery
from examples.crud_api.application.ListNotes.ListNotesResponse import ListNotesResponse
from examples.crud_api.domain.note.Note import Note


class ListNotesQueryHandler(IQueryHandler[ListNotesQuery], IScoped):
    """Handles ``ListNotesQuery`` — returns the 50 most recent notes.

    No pagination specification yet; extend with a ``PagingSpecification``
    when the table grows."""

    LIMIT = 50

    @inject
    def __init__(
        self,
        repository_provider: RepositoryProvider,
    ):
        self.repository_provider = repository_provider

    def handle(self, query: ListNotesQuery) -> ListNotesResponse:
        repo = self.repository_provider.get(Note)
        rows = (
            repo.table.order_by(Note.CreateUserTime.desc())
            .limit(self.LIMIT)
            .all()
        )
        response = ListNotesResponse()
        response.Data = [self._to_dto(row) for row in rows]
        return response

    @staticmethod
    def _to_dto(entity: Note) -> ListNoteDto:
        dto = ListNoteDto()
        dto.Id = str(entity.Id) if entity.Id is not None else None
        dto.Title = entity.Title
        dto.Body = entity.Body
        dto.CreateUserTime = (
            entity.CreateUserTime.isoformat()
            if entity.CreateUserTime is not None
            else None
        )
        return dto
