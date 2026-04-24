from injector import inject

from pdip.cqrs import ICommandHandler
from pdip.data.repository import RepositoryProvider
from pdip.dependency import IScoped

from examples.crud_api.application.CreateNote.CreateNoteCommand import (
    CreateNoteCommand,
)
from examples.crud_api.domain.note.Note import Note


class CreateNoteCommandHandler(ICommandHandler[CreateNoteCommand], IScoped):
    """Handles ``CreateNoteCommand`` — persists a ``Note`` row."""

    @inject
    def __init__(
        self,
        repository_provider: RepositoryProvider,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.repository_provider = repository_provider

    def handle(self, command: CreateNoteCommand):
        note = Note(Title=command.request.Title, Body=command.request.Body)
        self.repository_provider.get(Note).insert(note)
        self.repository_provider.commit()
