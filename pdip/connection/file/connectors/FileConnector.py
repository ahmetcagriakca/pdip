from abc import ABC, abstractmethod
from queue import Queue

from ....dependency.scopes import IScoped

from pandas import DataFrame


class FileConnector(ABC,IScoped):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def get_unpredicted_data(self, file: str, names: [], header: int, separator: str, limit: int, process_count:int, data_queue: Queue, result_queue:Queue):
        pass

    @abstractmethod
    def get_data_count(self, file: str):
        pass

    @abstractmethod
    def get_data(self, file: str, names: [], start: int, limit: int,
                  header: int, separator: str) -> DataFrame:
        pass

    @abstractmethod
    def write_data(self, file: str, data: DataFrame, separator: str):
        pass

    @abstractmethod
    def recreate_file(self, file: str, headers: [], separator: str):
        pass

    @abstractmethod
    def delete_file(self, file: str):
        pass
