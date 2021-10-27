import mysql.connector
from injector import inject

from .DatabaseConnector import DatabaseConnector
from ....configuration.models.database.database_config import DatabaseConfig


class MysqlDbConnector(DatabaseConnector):
    @inject
    def __init__(self, database_config: DatabaseConfig):
        self.database_config = database_config
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = mysql.connector.connect(user=self.database_config.user,
                                                  password=self.database_config.password,
                                                  database=self.database_config.database,
                                                  host=self.database_config.host,
                                                  port=self.database_config.port)
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

    def execute_many(self, query, data):
        try:
            self.cursor.prepare(query)
            self.cursor.executemany(None, data)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as error:
            self.connection.rollback()
            self.cursor.close()
            raise

    def get_table_count_query(self, query):
        count_query = f"SELECT COUNT (*)  \"COUNT\" FROM ({query})"
        return count_query

    def get_target_query_indexer(self):
        indexer = ':{index}'
        return indexer
