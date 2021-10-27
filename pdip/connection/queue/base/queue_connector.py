from abc import ABC, abstractmethod
from queue import Queue

from pandas import DataFrame

from ....dependency import IScoped


class QueueConnector(ABC, IScoped):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def delete_topic(self, topic_name):
        pass

    @abstractmethod
    def create_topic(self, topic_name):
        pass

    @abstractmethod
    def write_data(self, topic_name: str, messages: DataFrame):
        pass

    @abstractmethod
    def create_admin_client(self):
        pass

    @abstractmethod
    def create_producer(self):
        pass

    @abstractmethod
    def create_consumer(self, topic_name: str, auto_offset_reset: str, enable_auto_commit: bool, group_id: str):
        pass

    @abstractmethod
    def get_data(self, limit: int) -> DataFrame:
        pass

    @abstractmethod
    def get_unpredicted_data(self, limit: int, process_count: int, data_queue: Queue, result_queue: Queue) -> DataFrame:
        pass
