import json
import re
import time
from queue import Queue

import pandas as pd
from injector import inject

from .database_connector import DatabaseConnector
from .database_policy import DatabasePolicy
from ...models import DataQueueTask
from ....dependency import IScoped
from ....logging.loggers.console import ConsoleLogger


class DatabaseContext(IScoped):
    @inject
    def __init__(self,
                 database_policy: DatabasePolicy,
                 retry_count=3):
        self.connector: DatabaseConnector = database_policy.connector
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
    def fetch_query(self, query):
        self.connector.cursor.execute(query)
        columns = [column[0] for column in self.connector.cursor.description]
        results = []
        for row in self.connector.cursor.fetchall():
            results.append(dict(zip(columns, row)))
        # results =  self.connector.cursor.fetchall()
        return results

    def fetch(self, query):
        datas = self.fetch_query(query=query)
        # data_list = []
        # for data in datas:
        #     rows = []
        #     for row in data:
        #         rows.append(row)
        #     data_list.append(rows)
        return datas

    @connect
    def fetch_with_pd(self, query):
        data = pd.read_sql(sql=query, con=self.connector.connection)

        return data

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
                ConsoleLogger().error(f"Db write error on Error:{ex}")
                raise
            ConsoleLogger().error(
                f"Getting error on insert (Operation will be retried. Retry Count:{retry}). Error:{ex}")
            # retrying connect to db,
            self.connector.connect()
            time.sleep(1)
            return self._execute_with_retry(query=query, data=data, retry=retry + 1)

    @connect
    def get_table_count(self, query):
        count_query = self.connector.get_table_count_query(query=query)
        self.connector.cursor.execute(count_query)
        datas = self.connector.cursor.fetchall()
        return datas[0][0]

    def get_table_data(self, query):
        data_query = self.connector.get_table_data_query(query=query)
        return self.fetch(data_query)

    def get_table_data_with_paging(self, query, order_row, start, end):
        data_query = self.connector.get_table_data_with_paging_query(query=query, order_row=order_row, start=start,
                                                                     end=end)
        return self.fetch(data_query)

    def read_data(self, query: str, columns: [], limit: int):
        self.connector.connect()
        return pd.read_sql(query, con=self.connector.get_connection(), columns=columns, chunksize=limit)

    @connect
    def get_unpredicted_data(self, query: str, columns: [], limit: int, process_count: int, data_queue: Queue,
                             result_queue: Queue):
        total_data_count = 0
        transmitted_data_count = 0
        task_id = 0
        connection = self.connector.get_connection()
        for chunk in pd.read_sql(query, con=connection, columns=columns, chunksize=limit):
            data = json.loads(chunk.to_json(orient='records', date_format="iso"))
            task_id = task_id + 1
            data_count = len(chunk)
            total_data_count = total_data_count + data_count
            data_types = dict((c, chunk[c].dtype.name) for c in chunk.columns)
            # dict((c,df[c].dtype.name) for i in df.columns for j in i.items())
            data_queue_task = DataQueueTask(Id=task_id, Data=data, DataTypes=data_types,
                                            Start=total_data_count - data_count,
                                            End=total_data_count, Limit=limit, Message=f'query readed',
                                            IsFinished=False)
            data_queue.put(data_queue_task)
            transmitted_data_count = transmitted_data_count + 1
            if transmitted_data_count >= process_count:
                result = result_queue.get()
                if result:
                    transmitted_data_count = transmitted_data_count - 1
                else:
                    break

    def truncate_table(self, schema, table):
        truncate_query = self.connector.get_truncate_query(schema=schema, table=table)
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
            indexer = self.connector.get_target_query_indexer().format(index=index)
            target_query = self.replace_regex(target_query, column_row[1], indexer)
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
