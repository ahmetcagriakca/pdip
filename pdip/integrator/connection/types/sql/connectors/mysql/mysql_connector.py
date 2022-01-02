import mysql.connector
from injector import inject

from pdip.integrator.connection.domain.sql import SqlConnectionConfiguration
from ...base.sql_connector import SqlConnector


class MysqlConnector(SqlConnector):
    @inject
    def __init__(self, config: SqlConnectionConfiguration):
        self.config = config
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = mysql.connector.connect(user=self.config.BasicAuthentication.User,
                                                  password=self.config.BasicAuthentication.Password,
                                                  database=self.config.Database,
                                                  host=self.config.Server.Host,
                                                  port=self.config.Server.Port)
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
            raise

    def get_truncate_query(self, schema, table):
        count_query = f'TRUNCATE TABLE `{schema}`.`{table}`'
        return count_query

    def get_table_count_query(self, query):
        count_query = f"SELECT COUNT(*)  as \"COUNT\" FROM ({query})  as count_table"
        return count_query

    def get_table_select_query(self, selected_rows, schema, table):
        return f'SELECT {selected_rows} FROM `{schema}`.`{table}`'

    def get_target_query_indexer(self):
        indexer = '%s'
        return indexer

    def get_table_data_query(self, query):
        return f"SELECT * FROM ({query}) base_query"

    def get_table_data_with_paging_query(self, query, start, end):
        return f"SELECT * FROM (select * from ({query}) base_query order by null) ordered_query limit {end - start} offset {start}"
