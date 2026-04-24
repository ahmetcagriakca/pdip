"""Unit tests for the json helpers under ``pdip.json``.

``DateTimeEncoder``, ``UUIDEncoder`` and ``JsonConvert`` underpin
``@dtoclass`` / ``@request_class`` / ``@response_class`` (ADR-0013).
They also cross the multiprocess boundary, so any change in stdlib
``json`` behaviour between Python minor versions lands here first.
"""

import datetime
import json
import uuid
from unittest import TestCase

from pdip.json import DateTimeEncoder, UUIDEncoder
from pdip.json.base.json_convert import JsonConvert


class DateTimeEncoderSerialisesIsoFormat(TestCase):
    def test_datetime_is_encoded_as_isoformat_string(self):
        moment = datetime.datetime(2026, 4, 24, 13, 37, 42)
        payload = json.dumps({"at": moment}, cls=DateTimeEncoder)
        self.assertEqual(payload, '{"at": "2026-04-24T13:37:42"}')

    def test_non_datetime_falls_through_to_base_encoder(self):
        with self.assertRaises(TypeError):
            json.dumps({"v": object()}, cls=DateTimeEncoder)


class UUIDEncoderSerialisesHex(TestCase):
    def test_uuid_is_encoded_as_hex_string(self):
        uid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        payload = json.dumps({"id": uid}, cls=UUIDEncoder)
        self.assertEqual(payload, '{"id": "12345678123456781234567812345678"}')

    def test_non_uuid_falls_through_to_base_encoder(self):
        with self.assertRaises(TypeError):
            json.dumps({"v": object()}, cls=UUIDEncoder)


# A lightweight, self-contained DTO for the JsonConvert tests.
# We deliberately do not pull in the full ``@dtoclass`` stack so the
# test isolates behaviour of JsonConvert itself.
class _PointDto:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __iter__(self):
        yield from self.__dict__.items()

    def __eq__(self, other):
        return isinstance(other, _PointDto) and self.__dict__ == other.__dict__


class JsonConvertRegistersAndRoundTrips(TestCase):
    def setUp(self):
        # JsonConvert.mappings is class-level global state; snapshot and
        # restore so tests remain isolated.
        self._saved_mappings = dict(JsonConvert.mappings)

    def tearDown(self):
        JsonConvert.mappings = self._saved_mappings

    def test_register_returns_the_class(self):
        self.assertIs(JsonConvert.register(_PointDto), _PointDto)

    def test_tojson_then_fromjson_round_trips(self):
        JsonConvert.register(_PointDto)

        original = _PointDto(x=3, y=5)
        payload = JsonConvert.ToJSON(original)
        revived = JsonConvert.FromJSON(payload)

        self.assertEqual(revived, original)

    def test_class_mapper_raises_when_no_matching_class(self):
        # mappings snapshot excludes unknown shapes
        JsonConvert.mappings = {}
        with self.assertRaises(ValueError):
            JsonConvert.class_mapper({"unknown": 1, "fields": 2})
