from sqlalchemy import inspect

from ...base import SqlDialect, SqlConnector


class MysqlDialect(SqlDialect):
    def __init__(self, connector: SqlConnector):
        self.connector = connector

    @property
    def inspector(self):
        engine = self.connector.get_engine()
        return inspect(engine)

    @property
    def indexer(self) -> str:
        return '%s'

    @property
    def quotation_mark(self) -> str:
        return '`'

    def mark_to_object(self, o) -> str:
        return f'{self.quotation_mark}{o}{self.quotation_mark}'

    def get_table_count_query(self, schema, table):
        return f'SELECT COUNT(*) {self.mark_to_object("COUNT")} FROM {self.mark_to_object(schema)}.{self.mark_to_object(table)}'

    def get_count_query(self, query):
        return f'SELECT COUNT(*)  {self.mark_to_object("COUNT")} FROM ({query}) as count_table'

    def get_table_select_query(self, schema, table, selected_rows):
        return f'SELECT {selected_rows} FROM {self.mark_to_object(schema)}.{self.mark_to_object(table)}'

    def get_select_query(self, query):
        return f"SELECT * FROM ({query}) base_query"

    def get_table_data_with_paging_query(self, query, start, end):
        return f'''
SELECT * 
FROM (
    select * 
    from ({query}) base_query 
    order by null
    ) ordered_query 
limit {end - start} offset {start}
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
        return f'insert into {self.mark_to_object(schema)}.{self.mark_to_object(table)} values({values_query})'

    def get_insert_query(self, schema, table, columns_query, values_query):
        return f'insert into {self.mark_to_object(schema)}.{self.mark_to_object(table)}({columns_query}) values({values_query})'

    def prepare_insert_query(self, schema, table, columns=None, source_column_count: int = None):
        if schema is None or schema == '' or table is None or table == '':
            raise Exception(f"Schema and table required. {schema}.{table}")
        indexer_array = []
        for index in range(source_column_count):
            column_indexer = self.indexer.format(index=index)
            indexer_array.append(column_indexer)
        values_query = ','.join(indexer_array)
        query = self.get_insert_values_query(
            values_query=values_query,
            schema=schema,
            table=table
        )
        return query

    def get_create_table_query(self, schema, table, columns):
        query = f'''CREATE TABLE {self.mark_to_object(schema)}.{self.mark_to_object(table)} ('''
        column_queries = []
        for column in columns:
            name = f'{self.mark_to_object(column.Name)}'
            column_type = column.Type
            nullable = '' if not column.Nullable else "NULL"
            column_query = " ".join([name, column_type, nullable])
            column_queries.append(column_query)
        query += ",\n".join(column_queries)
        query += f''')'''
        return query

    def get_drop_table_query(self, schema, table):
        return f'DROP TABLE {self.mark_to_object(schema)}.{self.mark_to_object(table)}'

    def get_truncate_table_query(self, schema, table):
        return f'TRUNCATE TABLE {self.mark_to_object(schema)}.{self.mark_to_object(table)}'

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
