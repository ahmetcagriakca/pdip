import re
import time

from injector import inject

from .big_data_connector import BigDataConnector
from .big_data_dialect import BigDataDialect
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
    def fetch_query(self, query, excluded_columns=None):
        self.connector.cursor.execute(query)
        if excluded_columns is not None:
            columns = [column[0] for column in self.connector.cursor.description if column[0] not in excluded_columns]
        else:
            columns = [column[0] for column in self.connector.cursor.description]
        results = []
        for row in self.connector.cursor.fetchall():
            results.append(dict(zip(columns, row)))
        # results =  self.connector.cursor.fetchall()
        return results

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

    @connect
    def get_table_count(self, query):
        count_query = self.dialect.get_table_count_query(query=query)
        self.connector.cursor.execute(count_query)
        datas = self.connector.cursor.fetchall()
        return datas[0][0]

    def get_table_data(self, query):
        data_query = self.dialect.get_table_data_query(query=query)
        return self.fetch_query(data_query)

    def get_table_data_with_paging(self, query, start, end):
        data_query = self.dialect.get_table_data_with_paging_query(query=query,
                                                                     start=start,
                                                                     end=end)
        results = self.fetch_query(data_query, excluded_columns=['row_number'])

        return results

    def truncate_table(self, schema, table):
        truncate_query = self.dialect.get_truncate_query(schema=schema, table=table)
        return self.execute(query=truncate_query)

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
            indexer = self.dialect.get_target_query_indexer().format(index=index)
            target_query = self.replace_regex(target_query, column_row[0], indexer)
        return target_query

    def prepare_insert_row(self, data, column_rows):
        insert_rows = []
        for extracted_data in data:
            row = []
            for column_row in column_rows:
                prepared_data = extracted_data[column_rows.index(column_row)]
                row.append(prepared_data)
            insert_rows.append(tuple(row))
        return insert_rows
