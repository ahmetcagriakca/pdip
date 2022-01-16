import psycopg2
import psycopg2.extras as extras
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from ...base import SqlConnector
from .....domain.sql import SqlConnectionConfiguration


class PostgresqlConnector(SqlConnector):
    def __init__(self, config: SqlConnectionConfiguration):
        self.config = config
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = psycopg2.connect(host=self.config.Server.Host, port=self.config.Server.Port,
                                           user=self.config.BasicAuthentication.User,
                                           password=self.config.BasicAuthentication.Password,
                                           database=self.config.Database)
        self.cursor = self.connection.cursor()

    def disconnect(self):
        try:
            if self.cursor is not None:
                self.cursor.close()

            if self.connection is not None:
                self.connection.close()
        except Exception:
            pass

    def get_connection(self):
        return self.connection

    def get_engine_connection_url(self):
        connection_url = URL.create(
            "postgresql+psycopg2",
            username=self.config.BasicAuthentication.User,
            password=self.config.BasicAuthentication.Password,
            host=self.config.Server.Host,
            port=self.config.Server.Port,
            database=self.config.Database,
        )
        return connection_url

    def get_engine(self):
        connection_url = self.get_engine_connection_url()
        engine = create_engine(connection_url)
        return engine

    def execute_many(self, query, data):
        try:
            extras.execute_batch(self.cursor, query, data, 10000)
            self.connection.commit()
            return self.cursor.rowcount
        except (Exception, psycopg2.DatabaseError) as error:
            self.connection.rollback()
            self.cursor.close()
            raise
