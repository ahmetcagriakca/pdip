from pdip.integrator.connection.types.bigdata.base import BigDataDialect, BigDataConnector


class ImpalaDialect(BigDataDialect):
    def __init__(self, connector: BigDataConnector):
        self.connector = connector

    def get_target_query_indexer(self):
        indexer = '?'
        return indexer

    def get_truncate_query(self, schema, table):
        count_query = f'TRUNCATE TABLE {schema}.{table}'
        return count_query

    def get_table_count_query(self, query):
        count_query = f"SELECT COUNT(*) as COUNT  FROM ({query})  as count_table"
        return count_query

    def get_table_select_query(self, selected_rows, schema, table):
        return f'SELECT {selected_rows} FROM {schema}.{table}'

    def get_table_data_query(self, query):
        return f"SELECT * FROM ({query}) base_query"

    def get_table_data_with_paging_query(self, query, start, end):
        return f"SELECT * FROM ({query}) ordered_query   order by null limit {end - start} offset {start}"

    def get_insert_query(self, schema, table, values_query):
        return f'insert into {schema}.{table} values({values_query})'

    def get_schemas(self):
        # schemas = self.inspector.get_schema_names()
        return []

    def has_table(self, object_name, schema=None):
        # result = self.inspector.has_table(table_name=object_name, schema=schema)
        return ""

    def get_tables(self, schema):
        # tables = self.inspector.get_table_names(schema=schema)
        return []

    def get_sorted_table_and_fkc_names(self, schema):
        # tables = self.inspector.get_sorted_table_and_fkc_names(schema=schema)
        return []

    def get_views(self, schema):
        # views = self.inspector.get_view_names(schema=schema)
        return []

    def get_columns(self, schema, object_name):
        # columns = self.inspector.get_columns(table_name=object_name, schema=schema)
        return []
