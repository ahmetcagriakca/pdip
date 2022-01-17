from sqlalchemy import inspect

from ...base import SqlDialect, SqlConnector


class MysqlDialect(SqlDialect):
    def __init__(self, connector: SqlConnector):
        self.connector = connector
        self.engine = self.connector.get_engine()
        self.inspector = inspect(self.engine)

    def get_query_indexer(self):
        indexer = '%s'
        return indexer

    def get_truncate_query(self, schema, table):
        count_query = f'TRUNCATE TABLE `{schema}`.`{table}`'
        return count_query

    def get_table_count_query(self, query):
        count_query = f"SELECT COUNT(*)  as \"COUNT\" FROM ({query})  as count_table"
        return count_query

    def get_table_select_query(self, selected_rows, schema, table):
        return f'SELECT {selected_rows} FROM `{schema}`.`{table}`'

    def get_table_data_query(self, query):
        return f"SELECT * FROM ({query}) base_query"

    def get_table_data_with_paging_query(self, query, start, end):
        return f"SELECT * FROM (select * from ({query}) base_query order by null) ordered_query limit {end - start} offset {start}"

    def get_schemas(self):
        schemas = self.inspector.get_schema_names()
        return schemas

    def has_table(self, object_name, schema=None):
        result = self.inspector.has_table(table_name=object_name, schema=schema)
        return result

    def get_tables(self, schema):
        tables = self.inspector.get_table_names(schema=schema)
        return tables

    def get_views(self, schema):
        views = self.inspector.get_view_names(schema=schema)
        return views

    def get_columns(self, schema, object_name):
        columns = self.inspector.get_columns(table_name=object_name, schema=schema)
        return columns
