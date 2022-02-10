import cx_Oracle
from sqlalchemy import create_engine

from ...base import SqlConnector
from .....domain.sql import SqlConnectionConfiguration


class OracleConnector(SqlConnector):
    def __init__(self, config: SqlConnectionConfiguration):
        self.config = config
        self._tns = None
        self.connection_string = None
        self.connection = None
        self.cursor = None

    def connect(self):
        if self.config.Sid is not None and self.config.Sid != '':
            self._tns = cx_Oracle.makedsn(self.config.Server.Host, self.config.Server.Port,
                                          service_name=self.config.Sid)
        else:
            self._tns = cx_Oracle.makedsn(self.config.Server.Host, self.config.Server.Port,
                                          service_name=self.config.ServiceName)
        self.connection = cx_Oracle.connect(self.config.BasicAuthentication.User,
                                            self.config.BasicAuthentication.Password, self._tns,
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

    def get_engine_connection_url(self):
        if self.config.Sid is not None and self.config.Sid != '':
            connection_url = f'oracle+cx_oracle://{self.config.BasicAuthentication.User}:{self.config.BasicAuthentication.Password}@{self.config.Server.Host}:{self.config.Server.Port}/{self.config.Sid}'
        else:
            connection_url = f'oracle+cx_oracle://{self.config.BasicAuthentication.User}:{self.config.BasicAuthentication.Password}@{self.config.Server.Host}:{self.config.Server.Port}/{self.config.ServiceName}'
        return connection_url

    def get_engine(self):
        connection_url = self.get_engine_connection_url()
        engine = create_engine(connection_url)
        return engine

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
