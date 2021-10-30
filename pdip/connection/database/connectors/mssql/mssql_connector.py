import pyodbc

from ...base.database_connector import DatabaseConnector
from .....configuration.models.database import DatabaseConfig


class MssqlConnector(DatabaseConnector):
    def __init__(self, database_config: DatabaseConfig):
        self.database_config: DatabaseConfig = database_config
        # ;Client_CSet=UTF-8;Server_CSet=WINDOWS-1251
        if self.database_config.connection_string is not None and self.database_config.connection_string != '' and not self.database_config.connection_string.isspace():
            self.connection_string = self.database_config.connection_string
        else:
            if self.database_config.driver is None or  self.database_config.driver=='':
                self.database_config.driver = pyodbc.drivers()[0]
            self.connection_string = 'DRIVER={%s};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (
                self.database_config.driver, self.database_config.host, self.database_config.database,
                self.database_config.user, self.database_config.password)

        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = pyodbc.connect(self.connection_string)  # ,ansi=True)
        # self.connection.setencoding(encoding='utf-8')
        self.cursor = self.connection.cursor()
        self.cursor.setinputsizes([(pyodbc.SQL_WVARCHAR, 0, 0)])

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
        self.cursor.fast_executemany = True
        try:
            self.cursor.executemany(query, data)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as error:
            try:
                self.connection.rollback()
                self.cursor.fast_executemany = False
                self.cursor.executemany(query, data)
                self.connection.commit()
                return self.cursor.rowcount
            except Exception as error:
                self.connection.rollback()
                self.cursor.close()
                raise

    def get_target_query_indexer(self):
        indexer = '?'
        return indexer

    def prepare_data(self, data):
        # if data is not None and isinstance(data, str):
        #     data = data\
        #         .replace("ı", "i")\
        #         .replace("ş", "s")\
        #         .replace("ğ", "g")\
        #         .replace("İ", "I")\
        #         .replace("Ş","S")\
        #         .replace("Ğ", "G")
        return data
