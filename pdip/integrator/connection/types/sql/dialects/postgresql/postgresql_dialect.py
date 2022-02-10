from sqlalchemy import inspect

from ...base import SqlDialect, SqlConnector


class PostgresqlDialect(SqlDialect):
    def __init__(self, connector: SqlConnector):
        self.connector = connector

    @property
    def inspector(self):
        engine = self.connector.get_engine()
        return inspect(engine)

    def get_query_indexer(self):
        indexer = '%s'
        return indexer

    def get_truncate_query(self, schema, table):
        count_query = f'TRUNCATE TABLE "{schema}"."{table}"'
        return count_query

    def get_table_count_query(self, query):
        count_query = f"SELECT COUNT (*) as \"COUNT\"  FROM ({query})  as count_table"
        return count_query

    def get_table_select_query(self, selected_rows, schema, table):
        return f'SELECT {selected_rows} FROM "{schema}"."{table}"'

    def get_table_data_query(self, query):
        return f"SELECT * FROM ({query}) base_query"

    def get_table_data_with_paging_query(self, query, start, end):
        return f'''
WITH TEMP_INTEGRATION AS(
SELECT ordered_query.*,ROW_NUMBER() OVER ( order by (select null)) "row_number" 
FROM ({query}) ordered_query
) 
SELECT * 
FROM TEMP_INTEGRATION 
WHERE "row_number" > {start} AND "row_number" <= {end}
'''

    def prepare_select_query(self, schema, table, columns=None):
        if schema is None or schema == '' or table is None or table == '':
            raise Exception(f"Source Schema and Table required. {schema}.{table}")
        if columns is not None and len(columns) > 0:
            source_column_rows = [column.Name for column in columns]
            columns_query = ",".join(source_column_rows)
            query = self.get_table_select_query(selected_rows=columns_query, schema=schema,
                                                table=table)
        else:
            query = self.get_table_select_query(selected_rows='*', schema=schema, table=table)
        return query

    def get_insert_values_query(self, schema, table, values_query):
        return f'insert into "{schema}"."{table}" values({values_query})'

    def get_insert_query(self, schema, table, columns_query, values_query):
        return f'insert into "{schema}"."{table}"({columns_query}) values({values_query})'

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
