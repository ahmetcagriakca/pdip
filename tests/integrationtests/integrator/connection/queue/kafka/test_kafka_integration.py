"""Smoke integration test for the Kafka connector against a real
broker.

Boots assumes the caller (``tests/environments/kafka/docker-compose.yml``
locally, or the ``kafka:`` Actions service in CI) exposes a Kafka
broker on ``localhost:29092``. The broker is unauthenticated to match
the fixture; if a future fixture grows SASL, the ``auth=`` block
below should be filled in to match
``QueueProvider.get_context``'s key set.

Test surface kept narrow on purpose — this is a smoke-level check
that the adapter's public methods do round-trip messages through a
real broker. Deeper behaviours (SASL handshake, partitioning,
consumer-group rebalancing) are out of scope for the nightly job's
≤ 5-minute budget and would be better off in a dedicated harness.
"""

from queue import Queue
from unittest import TestCase
from uuid import uuid4

from pandas import DataFrame

from pdip.integrator.connection.types.queue.connectors.kafka_connector import KafkaConnector


# Match ``KAFKA_ADVERTISED_LISTENERS=PLAINTEXT_HOST://localhost:29092``
# from ``tests/environments/kafka/docker-compose.yml``. The CI job
# publishes the same port from its ``kafka:`` service container.
_BROKER = "localhost:29092"


class TestKafkaIntegration(TestCase):
    def setUp(self):
        # Per-test topic name avoids cross-test interference when the
        # CI job retries — a previous run's messages do not show up
        # in this run's consumer because the topic name is unique.
        self.topic_name = f"pdip_test_{uuid4().hex[:8]}"
        self.connector = KafkaConnector(servers=[_BROKER], auth=None)

    def tearDown(self):
        try:
            if self.connector.topic_exists(topic_name=self.topic_name):
                self.connector.delete_topic(topic_name=self.topic_name)
        except Exception:
            # Best-effort cleanup; do not let a teardown failure mask
            # the real assertion failure that triggered tearDown.
            pass
        try:
            self.connector.disconnect()
        except Exception:
            pass

    def test_create_topic_makes_topic_exist(self):
        self.assertFalse(self.connector.topic_exists(topic_name=self.topic_name))
        self.connector.create_topic(topic_name=self.topic_name)
        self.assertTrue(self.connector.topic_exists(topic_name=self.topic_name))

    def test_create_topic_is_idempotent(self):
        self.connector.create_topic(topic_name=self.topic_name)
        # Second call must not raise even though the topic already exists —
        # the connector swallows ``KafkaException("already exists")``.
        self.connector.create_topic(topic_name=self.topic_name)
        self.assertTrue(self.connector.topic_exists(topic_name=self.topic_name))

    def test_write_data_then_get_data_round_trips_messages(self):
        self.connector.create_topic(topic_name=self.topic_name)

        messages = DataFrame([
            {"id": 1, "name": "alpha"},
            {"id": 2, "name": "beta"},
            {"id": 3, "name": "gamma"},
        ])
        self.connector.write_data(topic_name=self.topic_name, messages=messages)

        # ``get_data`` blocks on ``_iter_messages`` which polls until
        # the broker stops returning new messages. ``earliest`` so the
        # consumer reads from the start of the topic, not the head of
        # the log — without this the just-produced messages would be
        # invisible because the default offset reset is ``latest``.
        self.connector.create_consumer(
            topic_name=self.topic_name,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id=f"pdip_test_consumer_{uuid4().hex[:8]}",
        )
        result = self.connector.get_data(limit=3)

        self.assertEqual(len(result), 3)
        self.assertEqual(sorted(result["id"].tolist()), [1, 2, 3])
        self.assertEqual(
            sorted(result["name"].tolist()),
            ["alpha", "beta", "gamma"],
        )

    def test_delete_topic_removes_topic(self):
        self.connector.create_topic(topic_name=self.topic_name)
        self.assertTrue(self.connector.topic_exists(topic_name=self.topic_name))

        self.connector.delete_topic(topic_name=self.topic_name)

        # Topic deletion in Kafka is asynchronous; ``list_topics`` may
        # still report the topic for a brief window. Poll for
        # absence with a bounded retry loop instead of asserting once.
        deleted = False
        for _ in range(20):
            if not self.connector.topic_exists(topic_name=self.topic_name):
                deleted = True
                break
            import time

            time.sleep(0.5)
        self.assertTrue(deleted, "topic was not removed within 10 s")
