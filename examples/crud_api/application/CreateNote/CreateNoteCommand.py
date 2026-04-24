from dataclasses import dataclass

from pdip.cqrs import ICommand
from examples.crud_api.application.CreateNote.CreateNoteRequest import (
    CreateNoteRequest,
)


@dataclass
class CreateNoteCommand(ICommand):
    """A unit of intent. The dispatcher resolves this to
    ``CreateNoteCommandHandler`` by convention — handlers are
    auto-discovered (ADR-0015)."""

    request: CreateNoteRequest = None
