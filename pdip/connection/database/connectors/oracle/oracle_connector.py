import cx_Oracle
from injector import inject

from ...base.database_connector import DatabaseConnector
from .....configuration.models.database import DatabaseConfig


class OracleConnector(DatabaseConnector):
    @inject
    def __init__(self, database_config: DatabaseConfig):
        self.database_config = database_config
        self._tns = None
        self.connection_string = None
        self.connection = None
        self.cursor = None

    def connect(self):
        if self.database_config.sid is not None and self.database_config.sid != '':
            self._tns = cx_Oracle.makedsn(self.database_config.host, self.database_config.port,
                                          service_name=self.database_config.sid)
        else:
            self._tns = cx_Oracle.makedsn(self.database_config.host, self.database_config.port,
                                          service_name=self.database_config.service_name)
        self.connection = cx_Oracle.connect(self.database_config.user, self.database_config.password, self._tns,
                                            encoding="UTF-8",
                                            nencoding="UTF-8")
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
