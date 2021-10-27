from __future__ import absolute_import

from injector import inject
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from ..configuration.models.database import DatabaseConfig
from ..dependency import IScoped
from ..utils.utils import Utils


class DatabaseSessionManager(IScoped):
    @inject
    def __init__(self,
                 database_config: DatabaseConfig):
        self.database_config = database_config
        self.engine = None
        self._SessionFactory = None
        self.session: Session = None
        self.connect()

    def __del__(self):
        # close = getattr(self, "close", None)
        # if callable(close):
        #     self.close()
        pass

    def connect(self):
        if self.database_config.type is not None:
            if self.database_config.connection_string is None or self.database_config.connection_string == '':
                self.database_config.connection_string = Utils.get_connection_string(
                    database_config=self.database_config)
            if self.database_config.type == 'SQLITE':
                self.engine = create_engine(self.database_config.connection_string,
                                            connect_args={"check_same_thread": False},
                                            poolclass=StaticPool,
                                            execution_options=self.database_config.execution_options)
            else:
                self.engine = create_engine(self.database_config.connection_string,
                                            poolclass=pool.NullPool,
                                            pool_pre_ping=True,
                                            connect_args={"application_name": self.database_config.application_name})
            self._SessionFactory = sessionmaker(bind=self.engine)
            self.session: Session = self.session_factory()

    def dispose(self):
        if self.engine is not None:
            self.engine.dispose()

    def close(self):
        if self.session is not None:
            self.session.close()
        if self.engine is not None:
            self.dispose()
            # self.engine = None

    def session_factory(self):
        if self._SessionFactory is not None:
            self.session = self._SessionFactory()
        return self.session

    def commit(self):
        if self.session is not None:
            self.session.commit()

    def rollback(self):
        if self.session is not None:
            self.session.flush()
            self.session.rollback()
