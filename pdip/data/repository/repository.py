import uuid
from datetime import datetime
from typing import Generic, List, TypeVar, Type

from injector import inject
from sqlalchemy.orm import Query

from ..base.database_session_manager import DatabaseSessionManager

T = TypeVar('T')


class Repository(Generic[T]):
    @inject
    def __init__(self, repository_type: Type[T], database_session_manager: DatabaseSessionManager):
        self.database_session_manager: DatabaseSessionManager = database_session_manager
        self.type = repository_type

    @property
    def table(self):
        return self.database_session_manager.session.query(self.type)

    def first(self, **kwargs) -> T:
        query: Query = self.table.filter_by(**kwargs)
        return query.first()

    def filter_by(self, **kwargs) -> List[T]:
        return self.table.filter_by(**kwargs)

    def get(self) -> List[T]:
        return self.table.all()

    def get_by_id(self, id: int) -> T:
        return self.table.filter_by(Id=id).first()

    def insert(self, entity: T):

        if entity.TenantId is None:
            if self.database_session_manager.engine.dialect.name == 'postgresql':
                entity.TenantId = uuid.UUID("00000000-0000-0000-0000-000000000000")
            else:
                entity.TenantId = str(uuid.UUID("00000000-0000-0000-0000-000000000000"))


        entity.CreateUserTime = datetime.now()
        if self.database_session_manager.engine.dialect.name == 'postgresql':
            entity.CreateUserId = uuid.UUID("00000000-0000-0000-0000-000000000000")
        else:
            entity.CreateUserId = str(uuid.UUID("00000000-0000-0000-0000-000000000000"))
        self.database_session_manager.session.add(entity)

    def update(self, entity: T):
        entity.UpdateUserTime = datetime.now()
        if self.database_session_manager.engine.dialect.name == 'postgresql':
            entity.UpdateUserId = uuid.UUID("00000000-0000-0000-0000-000000000000")
        else:
            entity.UpdateUserId = str(uuid.UUID("00000000-0000-0000-0000-000000000000"))

    def delete_by_id(self, id: int):
        entity = self.get_by_id(id)
        entity.GcRecId = uuid.uuid4()
        entity.UpdateUserTime = datetime.now()
        if self.database_session_manager.engine.dialect.name == 'postgresql':
            entity.UpdateUserId = uuid.UUID("00000000-0000-0000-0000-000000000000")
        else:
            entity.UpdateUserId = str(uuid.UUID("00000000-0000-0000-0000-000000000000"))

    def delete(self, entity: T):
        entity.GcRecId = uuid.uuid4()
        entity.UpdateUserTime = datetime.now()
        if self.database_session_manager.engine.dialect.name == 'postgresql':
            entity.UpdateUserId = uuid.UUID("00000000-0000-0000-0000-000000000000")
        else:
            entity.UpdateUserId = str(uuid.UUID("00000000-0000-0000-0000-000000000000"))

    def commit(self):
        self.database_session_manager.commit()
