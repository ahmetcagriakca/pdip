import os
import sqlite3

from pdip.integrator.connection.domain.types.inmemory import InMemoryConnectionConfiguration
from ...base import InMemoryConnector


class SqLiteConnector(InMemoryConnector):
    def __init__(self, config: InMemoryConnectionConfiguration):
        self.config = config
        self.connection_string = None
        if self.config.ConnectionString is not None:
            self.connection_string = self.config.ConnectionString
        else:
            database_directory = os.getcwd()
            self.connection_string = os.path.join(database_directory, self.config.Database)
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = sqlite3.connect(self.connection_string)
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
            self.cursor.executemany(query, data)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as error:
            self.connection.rollback()
            self.cursor.close()

    def get_target_query_indexer(self):
        indexer = '?'
        return indexer
