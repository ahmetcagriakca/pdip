"""Kafka source/target connector backed by
[`confluent-kafka`](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/).

Migrated from ``kafka-python`` per ADR-0022. Public surface stays the
same so upstream callers are not affected; the kafka-python-style
config keys that callers pass as ``auth`` are translated to
confluent-kafka's dotted keys at the adapter boundary.
"""

import json
import logging
from json import dumps
from queue import Queue
from typing import List

from confluent_kafka import Consumer, KafkaException, Producer
from confluent_kafka.admin import AdminClient, NewTopic
from pandas import DataFrame

from pdip.integrator.connection.domain.task import DataQueueTask
from ..base import QueueConnector

kafka_logger = logging.getLogger(name="confluent_kafka")
kafka_logger.setLevel(level=logging.WARNING)


# kafka-python used underscored keys such as ``sasl_plain_username``;
# confluent-kafka expects dotted keys like ``sasl.username``. Translate
# the handful of commonly used ones so existing callers keep working
# without editing their configuration.
_KAFKA_PYTHON_TO_CONFLUENT_KEYS = {
    "client_id": "client.id",
    "security_protocol": "security.protocol",
    "sasl_mechanism": "sasl.mechanism",
    "sasl_plain_username": "sasl.username",
    "sasl_plain_password": "sasl.password",
    "ssl_cafile": "ssl.ca.location",
    "ssl_certfile": "ssl.certificate.location",
    "ssl_keyfile": "ssl.key.location",
    "group_id": "group.id",
    "auto_offset_reset": "auto.offset.reset",
    "enable_auto_commit": "enable.auto.commit",
}


def _translate_keys(config: dict) -> dict:
    """Convert well-known kafka-python keys to their confluent-kafka
    equivalents. Keys that are already in dotted form (or not in the
    translation table) pass through unchanged."""

    if not config:
        return {}
    translated = {}
    for key, value in config.items():
        translated[_KAFKA_PYTHON_TO_CONFLUENT_KEYS.get(key, key)] = value
    return translated


def _servers_to_csv(servers) -> str:
    if isinstance(servers, str):
        return servers
    return ",".join(servers)


class KafkaConnector(QueueConnector):
    def __init__(self,
                 servers: List[str],
                 auth):
        self.auth = auth
        self.servers = servers
        self.data_frame = None
        self.client_id = "pdi_kafka_client"
        self.__admin: AdminClient = None
        self.__producer: Producer = None
        self.__consumer: Consumer = None
        self.connect()

    def connect(self):
        self.create_admin_client()
        self.create_producer()

    def disconnect(self):
        # confluent_kafka has no Python-level disconnect call; Producer
        # and Consumer clean up their native resources when garbage
        # collected or explicitly closed.
        try:
            if self.__producer is not None:
                self.__producer.flush()
        except Exception:
            pass
        try:
            if self.__consumer is not None:
                self.__consumer.close()
        except Exception:
            pass

    def _base_config(self) -> dict:
        config = {"bootstrap.servers": _servers_to_csv(self.servers)}
        if self.auth:
            config.update(_translate_keys(self.auth))
        return config

    def create_admin_client(self):
        self.__admin = AdminClient(self._base_config())

    def create_producer(self):
        config = self._base_config()
        config.setdefault("client.id", self.client_id)
        self.__producer = Producer(config)

    def create_consumer(self, topic_name: str, auto_offset_reset: str, enable_auto_commit: bool, group_id: str):
        config = self._base_config()
        config.update({
            "group.id": group_id,
            "auto.offset.reset": auto_offset_reset,
            "enable.auto.commit": enable_auto_commit,
        })
        self.__consumer = Consumer(config)
        self.__consumer.subscribe([topic_name])

    def _iter_messages(self, poll_timeout_s: float = 5.0):
        """Yield decoded message values until a poll returns ``None``
        (the confluent-kafka analogue of ``consumer_timeout_ms``)."""

        while True:
            message = self.__consumer.poll(timeout=poll_timeout_s)
            if message is None:
                return
            if message.error():
                raise KafkaException(message.error())
            value = message.value()
            if value is None:
                continue
            yield json.loads(value.decode("utf-8"))

    def get_unpredicted_data(self, limit: int, process_count: int, data_queue: Queue, result_queue: Queue) -> DataFrame:
        data = []
        total_data_count = 0
        limited_data_count = 0
        transmitted_data_count = 0
        task_id = 0
        for value in self._iter_messages():
            data.append(value)
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
        for value in self._iter_messages():
            data.append(value)
            data_count = data_count + 1
            if data_count >= limit:
                break
        df = DataFrame(data)
        return df

    def create_topic(self, topic_name):
        if not self.topic_exists(topic_name=topic_name):
            topic = NewTopic(topic_name, num_partitions=1, replication_factor=1)
            futures = self.__admin.create_topics([topic])
            # ``create_topics`` returns a dict of futures. Block until
            # each resolves; a pre-existing topic surfaces as a
            # KafkaException we can swallow for idempotency.
            for _, future in futures.items():
                try:
                    future.result()
                except KafkaException as ex:
                    if "already exists" in str(ex).lower():
                        print(f"{topic_name} Topic Exist")
                        continue
                    raise

    def topic_exists(self, topic_name) -> bool:
        metadata = self.__admin.list_topics(timeout=10)
        return topic_name in metadata.topics

    def delete_topic(self, topic_name):
        if self.topic_exists(topic_name=topic_name):
            response = self.__admin.delete_topics([topic_name])
            return response

    def write_data(self, topic_name: str, messages: DataFrame):
        for message in json.loads(messages.to_json(orient='records', date_format="iso")):
            self.__producer.produce(topic=topic_name, value=dumps(message).encode("utf-8"))
        self.__producer.flush()
