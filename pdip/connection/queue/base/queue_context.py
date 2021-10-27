from queue import Queue

from injector import inject
from pandas import DataFrame

from .queue_connector import QueueConnector
from ....dependency import IScoped


class QueueContext(IScoped):
    @inject
    def __init__(self,
                 connector: QueueConnector
                 ):
        self.connector: QueueConnector = connector

    def create_topic(self, topic_name):
        return self.connector.create_topic(topic_name=topic_name)

    def delete_topic(self, topic_name):
        return self.connector.delete_topic(topic_name=topic_name)

    def write_data(self, topic_name: str, messages: DataFrame):
        return self.connector.write_data(topic_name=topic_name, messages=messages)

    def get_unpredicted_data(self, topic_name: str, group_id: str, limit: int, process_count: int, data_queue: Queue,
                             result_queue: Queue,
                             auto_offset_reset: str = 'earliest',
                             enable_auto_commit: bool = True):
        self.connector.create_consumer(topic_name=topic_name, group_id=group_id, auto_offset_reset=auto_offset_reset,
                                       enable_auto_commit=enable_auto_commit)
        data = self.connector.get_unpredicted_data(limit=limit, process_count=process_count, data_queue=data_queue,
                                                   result_queue=result_queue)
        return data

    def get_data(self, topic_name: str, group_id: str, limit: int, auto_offset_reset: str = 'earliest',
                 enable_auto_commit: bool = True):
        self.connector.create_consumer(topic_name=topic_name, group_id=group_id, auto_offset_reset=auto_offset_reset,
                                       enable_auto_commit=enable_auto_commit)
        data = self.connector.get_data(limit=limit)
        return data

    def prepare_insert_row(self, data, column_rows):
        insert_rows = []
        for extracted_data in data:
            row = []
            for column_row in column_rows:
                prepared_data = extracted_data[column_rows.index(column_row)]
                row.append(prepared_data)
            insert_rows.append(tuple(row))
        return insert_rows
