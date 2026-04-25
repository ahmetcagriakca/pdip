from sqlalchemy import Column, String

from pdip.data.domain import Entity, EntityBase
from examples.crud_api.domain.base import Base


class NoteBase(EntityBase):
    """Plain-Python shape — audit/tenant columns come from EntityBase."""

    def __init__(
        self,
        Title: str = None,
        Body: str = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.Title = Title
        self.Body = Body


class Note(NoteBase, Entity, Base):
    """SQLAlchemy entity. ``Entity`` mixes in Id / audit columns and
    ``Base.metadata.create_all()`` wires the schema at boot. No
    ``__table_args__`` schema on this example — SQLite has no notion
    of schemas, and production deployments set one via a
    ``schema_translate_map`` in ``application.yml`` instead."""

    __tablename__ = "Note"

    Title = Column(String(300), index=False, unique=False, nullable=False)
    Body = Column(String(4000), index=False, unique=False, nullable=True)
