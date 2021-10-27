from typing import Type, TypeVar

from injector import inject
from sqlalchemy.orm import Query

from .database_session_manager import DatabaseSessionManager
from .repository import Repository
from ..configuration.models.database import DatabaseConfig
from ..dependency import IScoped

R = TypeVar('R')


class RepositoryProvider(IScoped):
    @inject
    def __init__(self,
                 database_config: DatabaseConfig,
                 database_session_manager: DatabaseSessionManager
                 ):
        self.database_config = database_config
        self.database_session_manager = database_session_manager

    # def __del__(self):
    #     self.close()

    def create(self) -> DatabaseSessionManager:
        if self.database_session_manager is None:
            self.database_session_manager = DatabaseSessionManager(database_config=self.database_config)
            return self.database_session_manager
        else:
            return self.database_session_manager

    def get(self, repository_type: Type[R]) -> Repository[R]:
        self.create()
        repository = Repository[repository_type](repository_type, self.database_session_manager)
        return repository

    def query(self, *entities, **kwargs) -> Query:
        database_session_manager = self.create()
        return database_session_manager.session.query(*entities, **kwargs)

    def commit(self):
        if self.database_session_manager is not None:
            self.database_session_manager.commit()

    def rollback(self):
        if self.database_session_manager is not None:
            self.database_session_manager.rollback()

    def reconnect(self):
        if self.database_session_manager is not None:
            self.database_session_manager.close()
            self.database_session_manager.connect()

    def close(self):
        if self.database_session_manager is not None:
            self.database_session_manager.close()
            # self.database_session_manager = None
