"""Unit tests for ``pdip.json.parsers.date_time_parser.date_time_parser``.

``date_time_parser`` is the object_hook used by ``JsonConvert`` to
revive ISO-8601 timestamps back into ``datetime`` instances. These
tests pin down the two recognised shapes (``T``-separated and
``space``-separated) plus the pass-through for non-matching values.
"""

from datetime import datetime
from unittest import TestCase

from pdip.json.parsers.date_time_parser import date_time_parser


class DateTimeParserRevivesIsoFormats(TestCase):
    def test_t_separated_string_is_converted_to_datetime(self):
        dct = {"at": "2026-04-24T12:30:45.123456"}

        result = date_time_parser(dct)

        self.assertIsInstance(result["at"], datetime)
        self.assertEqual(
            result["at"],
            datetime(2026, 4, 24, 12, 30, 45, 123456),
        )

    def test_space_separated_string_is_converted_to_datetime(self):
        dct = {"at": "2026-04-24 12:30:45.123456"}

        result = date_time_parser(dct)

        self.assertIsInstance(result["at"], datetime)
        self.assertEqual(
            result["at"],
            datetime(2026, 4, 24, 12, 30, 45, 123456),
        )

    def test_non_matching_string_is_left_alone(self):
        dct = {"greeting": "hello"}

        result = date_time_parser(dct)

        self.assertEqual(result["greeting"], "hello")

    def test_non_string_values_are_left_alone(self):
        dct = {"n": 42, "flag": True}

        result = date_time_parser(dct)

        self.assertEqual(result["n"], 42)
        self.assertEqual(result["flag"], True)

    def test_returns_same_dict_object(self):
        # The parser mutates and returns the same dict — not a copy.
        dct = {"at": "2026-04-24T12:30:45.000000"}

        result = date_time_parser(dct)

        self.assertIs(result, dct)
