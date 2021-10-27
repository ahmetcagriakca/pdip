import json
import logging
from json import dumps
from queue import Queue
from typing import List

from kafka import KafkaProducer, KafkaAdminClient, KafkaConsumer
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError
from pandas import DataFrame

from ..base import QueueConnector
from ...models import DataQueueTask

kafka_logger = logging.getLogger(name="kafka")
kafka_logger.setLevel(level=logging.WARNING)


class KafkaConnector(QueueConnector):
    def __init__(self,
                 servers: List[str],
                 auth):
        self.auth = auth
        self.servers = servers
        self.data_frame = None
        self.client_id = "pdi_kafka_client"
        self.__admin: KafkaAdminClient = None
        self.__producer: KafkaProducer = None
        self.__consumer: KafkaConsumer = None
        self.connect()

    def connect(self):
        # KAFKA_CLIENT_ID: str = "client_id"
        self.create_admin_client()
        self.create_producer()
        # self.__admin = KafkaAdminClient(bootstrap_servers=self.servers,
        #                                 **self.auth
        #                                 )
        # os.path.isdir(self.folder)
        pass

    def disconnect(self):
        pass
        # try:
        #     if self.file is not None:
        #         self.file.close()
        # except Exception:
        #     pass

    def create_admin_client(self):
        if self.auth is not None:
            self.__admin = KafkaAdminClient(bootstrap_servers=self.servers,
                                            **self.auth
                                            )
        elif self.auth is None:
            self.__admin = KafkaAdminClient(bootstrap_servers=self.servers,
                                            )

    def create_producer(self):
        if self.auth is not None:
            self.__producer = KafkaProducer(bootstrap_servers=list(self.servers),
                                            client_id=self.client_id,
                                            value_serializer=lambda x: dumps(x).encode('utf-8'),
                                            **self.auth)
        elif self.auth is None:
            self.__producer = KafkaProducer(bootstrap_servers=list(self.servers),
                                            client_id=self.client_id,
                                            value_serializer=lambda x: dumps(x).encode('utf-8'))

    def create_consumer(self, topic_name: str, auto_offset_reset: str, enable_auto_commit: bool, group_id: str):
        # KAFKA_CONSUMER_GROUP_ID: str = "consumer_group_id"
        # KAFKA_AUTO_OFFSET_RESET: str = "earliest"
        # KAFKA_ENABLE_AUTO_COMMIT: bool = True
        if self.auth is not None:
            self.__consumer = KafkaConsumer(topic_name, bootstrap_servers=list(self.servers),
                                            consumer_timeout_ms=5000,
                                            auto_offset_reset=auto_offset_reset,
                                            enable_auto_commit=enable_auto_commit,
                                            group_id=group_id,
                                            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                                            **self.auth)
        if self.auth is None:
            self.__consumer = KafkaConsumer(topic_name, bootstrap_servers=list(self.servers),
                                            consumer_timeout_ms=5000,
                                            auto_offset_reset=auto_offset_reset,
                                            enable_auto_commit=enable_auto_commit,
                                            group_id=group_id,
                                            value_deserializer=lambda x: json.loads(x.decode('utf-8')))

    def get_unpredicted_data(self, limit: int, process_count: int, data_queue: Queue, result_queue: Queue) -> DataFrame:
        data = []
        total_data_count = 0
        limited_data_count = 0
        transmitted_data_count = 0
        task_id = 0
        for message in self.__consumer:
            data.append(message.value)
            total_data_count = total_data_count + 1
            limited_data_count = limited_data_count + 1
            if limited_data_count >= limit:
                task_id = task_id + 1
                data_queue_task = DataQueueTask(Id=task_id, Data=data, Start=total_data_count - limited_data_count,
                                                End=total_data_count, Limit=limit, IsFinished=False)
                data_queue.put(data_queue_task)
                transmitted_data_count = transmitted_data_count + 1
                limited_data_count = 0
                data = []
                if transmitted_data_count >= process_count:
                    result = result_queue.get()
                    if result:
                        transmitted_data_count = transmitted_data_count - 1
                    else:
                        break

        if data is not None and len(data) > 0:
            task_id = task_id + 1
            total_data_count = total_data_count + len(data)
            data_queue_task = DataQueueTask(Id=task_id, Data=data, Start=total_data_count - limited_data_count,
                                            End=total_data_count, Limit=limit, IsFinished=False)
            data_queue.put(data_queue_task)

    def get_data(self, limit: int) -> DataFrame:
        data = []
        data_count = 0
        for message in self.__consumer:

            data.append(message.value)
            data_count = data_count + 1
            if data_count >= limit:
                break
        df = DataFrame(data)
        return df

    def create_topic(self, topic_name):
        # KAFKA_TOPIC_NUM_PARTITIONS: int = 3
        # KAFKA_TOPIC_REPLICA_FACTOR: int = 3
        if not self.topic_exists(topic_name=topic_name):
            try:
                topic = [NewTopic(name=topic_name, num_partitions=1, replication_factor=1)]
                response = self.__admin.create_topics(new_topics=topic, validate_only=False)
            except TopicAlreadyExistsError as ex:
                print(f"{topic_name} Topic Exist")

    def topic_exists(self, topic_name) -> bool:
        topic_metadata = self.__admin.list_topics()
        return topic_name in topic_metadata

    def delete_topic(self, topic_name):
        if self.topic_exists(topic_name=topic_name):
            response = self.__admin.delete_topics([topic_name])
            return response

    def write_data(self, topic_name: str, messages: DataFrame):
        for message in json.loads(messages.to_json(orient='records', date_format="iso")):
            response = self.__producer.send(topic=topic_name, value=message)
