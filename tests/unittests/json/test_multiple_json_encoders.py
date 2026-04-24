"""Unit tests for ``pdip.json.encoders.mutliple_json_encoders.MultipleJsonEncoders``.

The combiner walks a list of ``JSONEncoder`` subclasses and returns
the first encoder that succeeds. When none do, it raises
``TypeError`` naming the offending type.
"""

import json
from datetime import datetime
from unittest import TestCase

from pdip.json.encoders.date_time_encoder import DateTimeEncoder
from pdip.json.encoders.mutliple_json_encoders import MultipleJsonEncoders
from pdip.json.encoders.uuid_encoder import UUIDEncoder


class _Unserialisable:
    """A class none of the known encoders can handle."""

    pass


class MultipleJsonEncodersRaisesWhenNoneMatch(TestCase):
    def test_raises_type_error_for_type_no_encoder_handles(self):
        # Arrange — combine the datetime + UUID encoders; neither
        # handles a ``_Unserialisable`` instance.
        encoder = MultipleJsonEncoders(DateTimeEncoder, UUIDEncoder)

        # Act / Assert
        with self.assertRaises(TypeError) as ctx:
            json.dumps({"v": _Unserialisable()}, cls=encoder)

        self.assertIn("_Unserialisable", str(ctx.exception))

    def test_accepts_handled_type_via_first_encoder(self):
        # Sanity: the combiner still serialises a datetime through
        # the first encoder in the chain.
        encoder = MultipleJsonEncoders(DateTimeEncoder, UUIDEncoder)
        moment = datetime(2026, 4, 24, 10, 0, 0)

        payload = json.dumps({"ts": moment}, cls=encoder)

        self.assertIn(moment.isoformat(), payload)
