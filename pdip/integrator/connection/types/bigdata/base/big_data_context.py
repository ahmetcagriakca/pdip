import re
import time

from injector import inject

from .big_data_connector import BigDataConnector
from .big_data_dialect import BigDataDialect
from .big_data_iterator import BigDataIterator
from .big_data_policy import BigDataPolicy
from ......dependency import IScoped


class BigDataContext(IScoped):
    @inject
    def __init__(self,
                 policy: BigDataPolicy,
                 retry_count=3):
        self.connector: BigDataConnector = policy.connector
        self.dialect: BigDataDialect = policy.dialect
        self.retry_count = retry_count
        self.default_retry = 1

    def connect(func):
        def inner(*args, **kwargs):
            try:
                args[0].connector.connect()
                return func(*args, **kwargs)
            finally:
                args[0].connector.disconnect()

        return inner

    @connect
    def get_query_columns(self, query, excluded_columns=None):
        self.connector.cursor.execute(query)
        if excluded_columns is not None:
            columns = [column[0] for column in self.connector.cursor.description if
                       column[0] not in excluded_columns]
        else:
            columns = [column[0] for column in self.connector.cursor.description]
        return columns

    @connect
    def fetch_query(self, query, excluded_columns=None):
        self.connector.cursor.execute(query)
        if excluded_columns is not None:
            columns = [column[0] for column in self.connector.cursor.description if column[0] not in excluded_columns]
        else:
            columns = [column[0] for column in self.connector.cursor.description]
        results = []
        for row in self.connector.cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results

    @connect
    def get_table_count(self, schema, table):
        count_query = self.dialect.get_table_count_query(schema=schema, table=table)
        self.connector.cursor.execute(count_query)
        datas = self.connector.cursor.fetchall()
        return datas[0][0]

    @connect
    def get_count_for_query(self, query):
        count_query = self.dialect.get_count_query(query=query)
        self.connector.cursor.execute(count_query)
        datas = self.connector.cursor.fetchall()
        return datas[0][0]

    def get_table_data(self, schema, table, columns=None):
        data_query = self.dialect.prepare_select_query(schema=schema, table=table, columns=columns)
        return self.fetch_query(data_query)

    def get_data_for_query(self, query):
        data_query = self.dialect.get_select_query(query=query)
        return self.fetch_query(data_query)

    def get_data_with_paging(self, query, start, end):
        data_query = self.dialect.get_paging_query(
            query=query,
            start=start,
            end=end
        )
        results = self.fetch_query(data_query, excluded_columns=['row_number'])
        return results

    def get_iterator_for_query(self, query, limit):
        data_query = self.dialect.get_select_query(query=query)
        iterator = BigDataIterator(connector=self.connector, query=data_query, limit=limit)
        return iterator

    def get_iterator(self, schema, table, columns=None, limit=0):
        data_query = self.dialect.prepare_select_query(schema=schema, table=table, columns=columns)
        iterator = BigDataIterator(connector=self.connector, query=data_query, limit=limit)
        return iterator

    @connect
    def execute(self, query) -> any:
        self.connector.cursor.execute(query)
        self.connector.connection.commit()
        return self.connector.cursor.rowcount

    @connect
    def execute_many(self, query, data):
        return self._execute_with_retry(query=query, data=data, retry=self.default_retry)

    def _execute_many_start(self, query, data):
        return self.connector.execute_many(query=query, data=data)

    def _execute_with_retry(self, query, data, retry):
        try:
            return self._execute_many_start(query=query, data=data)
        except Exception as ex:
            if retry > self.retry_count:
                print(f"Db write error on Error:{ex}")
                raise
            print(
                f"Getting error on insert (Operation will be retried. Retry Count:{retry}). Error:{ex}")
            # retrying connect to db,
            self.connector.connect()
            time.sleep(1)
            return self._execute_with_retry(query=query, data=data, retry=retry + 1)

    def create_table(self, schema, table, columns, if_exists=None):
        query = self.dialect.get_create_table_query(schema=schema, table=table, columns=columns, if_exists=if_exists)
        return self.execute(query=query)

    def drop_table(self, schema, table):
        query = self.dialect.get_drop_table_query(schema=schema, table=table)
        return self.execute(query=query)

    def truncate_table(self, schema, table):
        query = self.dialect.get_truncate_table_query(schema=schema, table=table)
        return self.execute(query=query)

    @staticmethod
    def replace_regex(text, field, indexer):
        text = re.sub(r'\(:' + field + r'\b', f'({indexer}', text)
        text = re.sub(r':' + field + r'\b\)', f'{indexer})', text)
        text = re.sub(r':' + field + r'\b', f'{indexer}', text)
        return text

    def prepare_target_query(self, column_rows, query):
        target_query = query
        for column_row in column_rows:
            index = column_rows.index(column_row)
            indexer = self.dialect.indexer.format(index=index)
            target_query = self.replace_regex(target_query, column_row[0], indexer)
        return target_query

    def prepare_insert_row(self, data, columns):
        insert_rows = []
        for extracted_data in data:
            row = []
            for column_row in columns:
                prepared_data = extracted_data[column_row]
                row.append(prepared_data)
            insert_rows.append(tuple(row))
        return insert_rows

    def _get_values_query(self, source_column_count):
        indexer_array = []
        for index in range(source_column_count):
            column_indexer = self.dialect.indexer.format(index=index)
            indexer_array.append(column_indexer)
        values_query = ','.join(indexer_array)
        return values_query

    def get_target_query(self, query, source_columns, target_columns, schema, table, source_column_count):
        if query is not None:
            if source_columns is not None and len(source_columns) > 0:
                column_rows = source_columns
                query = self.prepare_target_query(
                    column_rows=column_rows,
                    query=query
                )
            else:
                if schema is None or schema == '' or table is None or table == '':
                    raise Exception(f"Schema and table required. {schema}.{table}")
                values_query = self._get_values_query(source_column_count)
                query = self.dialect.get_insert_values_query(
                    values_query=values_query,
                    schema=schema,
                    table=table
                )
        else:
            if source_columns is not None and len(source_columns) > 0:
                if schema is None or schema == '' or table is None or table == '':
                    raise Exception(f"Schema and table required. {schema}.{table}")
                target_column_rows = [self.dialect.mark_to_object(column) for column in target_columns]
                columns_query = ','.join(target_column_rows)
                values_query = self._get_values_query(source_column_count)
                query = self.dialect.get_insert_query(
                    columns_query=columns_query,
                    values_query=values_query,
                    schema=schema,
                    table=table
                )
            else:
                if schema is None or schema == '' or table is None or table == '':
                    raise Exception(f"Schema and table required. {schema}.{table}")
                values_query = self._get_values_query(source_column_count)
                query = self.dialect.get_insert_values_query(
                    values_query=values_query,
                    schema=schema,
                    table=table
                )
        return query

    def get_insert_values(self, columns):
        insert_row_values = ''
        for column in columns:
            insert_row_values += f'{"" if column == columns[0] else ", "}:{column.Name}'
        return insert_row_values

    def get_insert_columns(self, columns):
        insert_row_columns = ''
        for column in columns:
            insert_row_columns += f'{"" if column == columns[0] else ", "}{self.dialect.mark_to_object(column.Name)}'
        return insert_row_columns

    def generate_insert_query(self, schema, table, source_columns, target_columns):
        insert_values = self.get_insert_values(source_columns)
        insert_columns = self.get_insert_columns(target_columns)
        query = self.dialect.get_insert_query(schema=schema, table=table, columns_query=insert_columns,
                                              values_query=insert_values)
        return query
