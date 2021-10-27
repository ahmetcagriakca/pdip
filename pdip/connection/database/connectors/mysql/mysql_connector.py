import mysql.connector
from injector import inject

from ...base.database_connector import DatabaseConnector
from .....configuration.models.database import DatabaseConfig


class MysqlDbConnector(DatabaseConnector):
    @inject
    def __init__(self, database_config: DatabaseConfig):
        self.database_config = database_config
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = mysql.connector.connect(user=self.database_config.username,
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

    def get_table_data_with_paging_query(self, query, order_row, start, end):
        return f"SELECT * FROM ({query} order by `{order_row}`) ordered_query limit {end - start} offset {start}"
