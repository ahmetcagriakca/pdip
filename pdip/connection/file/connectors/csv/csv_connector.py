import csv
import json
import os
from queue import Queue

import pandas as pd
from pandas import DataFrame

from ...base import FileConnector
from ....models import DataQueueTask


class CsvConnector(FileConnector):
    def __init__(self,
                 host: str):
        self.host = host
        self.data_frame = None

    def connect(self):
        # os.path.isdir(self.folder)
        pass

    def disconnect(self):
        pass
        # try:
        #     if self.file is not None:
        #         self.file.close()
        # except Exception:
        #     pass

    def get_unpredicted_data(self, file: str, names: [], header: int, separator: str, limit: int, process_count: int,
                             data_queue: Queue,
                             result_queue: Queue):
        file_path = file
        total_data_count = 0
        transmitted_data_count = 0
        task_id = 0
        for chunk in pd.read_csv(file_path, names=names, decimal=',', sep=separator, header=header, chunksize=limit,
                                 iterator=True, low_memory=False):
            data = json.loads(chunk.to_json(orient='records', date_format="iso"))
            task_id = task_id + 1
            data_count = len(chunk)
            total_data_count = total_data_count + data_count
            data_queue_task = DataQueueTask(Id=task_id, Data=data, Start=total_data_count - data_count,
                                            End=total_data_count, Limit=limit, Message=f'{file_path} file readed',
                                            IsFinished=False)
            data_queue.put(data_queue_task)
            transmitted_data_count = transmitted_data_count + 1
            if transmitted_data_count >= process_count:
                result = result_queue.get()
                if result:
                    transmitted_data_count = transmitted_data_count - 1
                else:
                    break

    def get_data_count(self, file: str):
        file_path = os.path.join(self.host, file)
        with open(file_path, 'rb') as f:
            count = sum(1 for line in f)
        return count

    def get_data(self, file: str, names: [], start: int, limit: int, header: int,
                 separator: str) -> DataFrame:
        file_path = os.path.join(self.host, file)
        count = 0
        for chunk in pd.read_csv(file_path, names=names, sep=separator, header=header, chunksize=limit, iterator=True,
                                 low_memory=False):
            count += len(chunk)
            if start < count:
                return chunk

        return None

    def write_data(self, file: str, data: DataFrame, separator: str):
        file_path = os.path.join(self.host, file)
        data.to_csv(file_path, mode='a', header=0, sep=separator, index=False)

    def recreate_file(self, file: str, headers: [], separator: str):
        self.delete_file(file=file)
        file_path = os.path.join(self.host, file)
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=separator)
            writer.writerow(headers)

    def delete_file(self, file: str):
        file_path = os.path.join(self.host, file)
        if os.path.exists(file_path):
            os.remove(file_path)
