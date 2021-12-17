import psycopg2
import psycopg2.extras as extras
from injector import inject

from pdip.integrator.connection.domain.sql import SqlConnectionConfiguration
from ...base.sql_connector import SqlConnector


class PostgresqlConnector(SqlConnector):
    @inject
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

    def execute_many(self, query, data):
        try:
            extras.execute_batch(self.cursor, query, data, 10000)
            self.connection.commit()
            return self.cursor.rowcount
        except (Exception, psycopg2.DatabaseError) as error:
            self.connection.rollback()
            self.cursor.close()
            raise

    def get_table_count_query(self, query):
        count_query = f"SELECT COUNT (*)  as \"COUNT\" FROM ({query})  as count_table"
        return count_query

    def get_target_query_indexer(self):
        indexer = '%s'
        return indexer
