"""Unit tests for the Kafka connector after the ``confluent-kafka``
migration (see ADR-0022).

The ``queue`` subpackage has a pre-existing circular import between
``connectors/__init__.py`` and ``base/queue_provider.py``. In normal
pdip usage the cycle resolves lazily once both packages finish loading.
To exercise ``kafka_connector`` in isolation we stub the parent
packages' ``__init__`` modules and load the connector file directly,
avoiding the package-level chain.

``confluent_kafka`` and ``pandas`` are also stubbed so the tests do not
require librdkafka or pandas to run on CI.
"""

import importlib.util
import pathlib
import sys
import types
from unittest import TestCase
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


def _ensure_stub(name, **attrs):
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


def _install_stubs():
    # confluent_kafka + admin submodule with just the symbols the
    # connector imports at module top.
    class _KafkaException(Exception):
        pass

    _ensure_stub(
        "confluent_kafka",
        Producer=MagicMock(name="Producer"),
        Consumer=MagicMock(name="Consumer"),
        KafkaException=_KafkaException,
    )
    _ensure_stub(
        "confluent_kafka.admin",
        AdminClient=MagicMock(name="AdminClient"),
        NewTopic=MagicMock(name="NewTopic"),
    )

    # pandas DataFrame stub (only the identity is touched in tests).
    _ensure_stub("pandas", DataFrame=MagicMock(name="DataFrame"))

    # Short-circuit the queue.base package init so the connector's
    # ``from ..base import QueueConnector`` resolves without loading
    # queue_provider (which triggers the circular import).
    class _QueueConnector:
        pass

    base_pkg = _ensure_stub(
        "pdip.integrator.connection.types.queue.base",
        QueueConnector=_QueueConnector,
    )
    base_pkg.__path__ = []  # mark as a package so relative imports work

    # DataQueueTask lives on a real submodule; import is fine normally,
    # but stubbing it removes the need to load the whole domain tree.
    _ensure_stub(
        "pdip.integrator.connection.domain.task",
        DataQueueTask=MagicMock(name="DataQueueTask"),
    )
    # Ensure the intermediate package modules exist as package objects
    # so the dotted import path resolves.
    for dotted in (
        "pdip.integrator.connection.domain",
        "pdip.integrator.connection.types.queue",
    ):
        pkg = _ensure_stub(dotted)
        if not hasattr(pkg, "__path__"):
            pkg.__path__ = []


_install_stubs()


def _load_connector_module():
    path = (
        pathlib.Path(__file__).resolve().parents[6]
        / "pdip" / "integrator" / "connection" / "types" / "queue"
        / "connectors" / "kafka_connector.py"
    )
    spec = importlib.util.spec_from_file_location(
        "pdip.integrator.connection.types.queue.connectors.kafka_connector",
        path,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_kc = _load_connector_module()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TranslateKeysNormalisesKafkaPythonNames(TestCase):
    def test_known_kafka_python_keys_become_dotted(self):
        translated = _kc._translate_keys({
            "client_id": "c",
            "group_id": "g",
            "security_protocol": "SASL_SSL",
            "sasl_mechanism": "PLAIN",
            "sasl_plain_username": "u",
            "sasl_plain_password": "p",
            "auto_offset_reset": "earliest",
            "enable_auto_commit": False,
        })
        self.assertEqual(translated, {
            "client.id": "c",
            "group.id": "g",
            "security.protocol": "SASL_SSL",
            "sasl.mechanism": "PLAIN",
            "sasl.username": "u",
            "sasl.password": "p",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        })

    def test_unknown_keys_pass_through(self):
        self.assertEqual(
            _kc._translate_keys({"custom.key": 1, "future_option": 2}),
            {"custom.key": 1, "future_option": 2},
        )

    def test_none_or_empty_auth_returns_empty_dict(self):
        self.assertEqual(_kc._translate_keys(None), {})
        self.assertEqual(_kc._translate_keys({}), {})


class ServersToCsvAcceptsBothShapes(TestCase):
    def test_list_becomes_comma_separated_string(self):
        self.assertEqual(_kc._servers_to_csv(["a:9092", "b:9092"]), "a:9092,b:9092")

    def test_string_passes_through(self):
        self.assertEqual(_kc._servers_to_csv("a:9092,b:9092"), "a:9092,b:9092")


class KafkaConnectorUsesConfluentKafka(TestCase):
    def setUp(self):
        self.producer_cls = MagicMock(name="ProducerCls")
        self.consumer_cls = MagicMock(name="ConsumerCls")
        self.admin_cls = MagicMock(name="AdminCls")
        self.new_topic_cls = MagicMock(name="NewTopicCls")

        self._patches = [
            patch.object(_kc, "Producer", self.producer_cls),
            patch.object(_kc, "Consumer", self.consumer_cls),
            patch.object(_kc, "AdminClient", self.admin_cls),
            patch.object(_kc, "NewTopic", self.new_topic_cls),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()

    def test_producer_config_uses_dotted_keys_and_default_client_id(self):
        _kc.KafkaConnector(servers=["h:1"], auth={"sasl_mechanism": "PLAIN"})

        config = self.producer_cls.call_args.args[0]
        self.assertEqual(config["bootstrap.servers"], "h:1")
        self.assertEqual(config["sasl.mechanism"], "PLAIN")
        self.assertEqual(config["client.id"], "pdi_kafka_client")

    def test_admin_client_receives_bootstrap_servers(self):
        _kc.KafkaConnector(servers=["h1:1", "h2:1"], auth=None)
        config = self.admin_cls.call_args.args[0]
        self.assertEqual(config["bootstrap.servers"], "h1:1,h2:1")

    def test_create_consumer_subscribes_to_topic(self):
        connector = _kc.KafkaConnector(servers=["h:1"], auth=None)
        consumer_instance = self.consumer_cls.return_value

        connector.create_consumer(
            topic_name="events",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            group_id="my-group",
        )

        config = self.consumer_cls.call_args.args[0]
        self.assertEqual(config["group.id"], "my-group")
        self.assertEqual(config["auto.offset.reset"], "earliest")
        self.assertEqual(config["enable.auto.commit"], False)
        consumer_instance.subscribe.assert_called_once_with(["events"])

    def test_create_topic_is_idempotent_on_already_exists(self):
        connector = _kc.KafkaConnector(servers=["h:1"], auth=None)
        admin_instance = self.admin_cls.return_value
        metadata = MagicMock()
        metadata.topics = {}
        admin_instance.list_topics.return_value = metadata

        future = MagicMock()
        future.result.side_effect = _kc.KafkaException("Topic already exists")
        admin_instance.create_topics.return_value = {"t": future}

        connector.create_topic("t")  # must not raise
        admin_instance.create_topics.assert_called_once()

    def test_write_data_flushes_after_produce(self):
        connector = _kc.KafkaConnector(servers=["h:1"], auth=None)
        producer_instance = self.producer_cls.return_value

        class _Frame:
            def to_json(self, orient, date_format):
                return '[{"x": 1}, {"x": 2}]'

        connector.write_data("t", _Frame())
        self.assertEqual(producer_instance.produce.call_count, 2)
        producer_instance.flush.assert_called_once()

    def test_disconnect_flushes_producer_and_closes_consumer(self):
        connector = _kc.KafkaConnector(servers=["h:1"], auth=None)
        connector.create_consumer("t", "earliest", True, "g")
        producer_instance = self.producer_cls.return_value
        consumer_instance = self.consumer_cls.return_value

        connector.disconnect()

        producer_instance.flush.assert_called()
        consumer_instance.close.assert_called_once()
