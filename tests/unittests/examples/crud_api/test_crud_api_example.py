"""End-to-end test that boots the ``examples/crud_api`` app and
exercises its CQRS + REST flow. Keeps the example in sync with the
framework — CI will flag any import / boot / endpoint regression the
moment it lands, so the example never rots.

The test deliberately uses a ``root_directory`` pointing at the
example's own tree so Pdi's auto-discovery walks just the example
(not the whole repo) — mirroring what ``python examples/crud_api/main.py``
does when a contributor runs it locally.
"""

import json
import os
import shutil
from unittest import TestCase

from pdip.api.app import FlaskAppWrapper
from pdip.base import Pdi
from pdip.data.base import DatabaseSessionManager

from examples.crud_api.domain.base import Base

_EXAMPLE_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "..", "..", "examples", "crud_api",
    )
)


class CrudApiExampleBootsAndExposesCqrsEndpoints(TestCase):
    """Boots ``examples/crud_api`` exactly as ``main.py`` would, then
    drives the REST surface via Flask's test client so we never need
    to open a real port."""

    def setUp(self):
        try:
            self.pdi = Pdi(root_directory=_EXAMPLE_ROOT)
            engine = self.pdi.get(DatabaseSessionManager).engine
            Base.metadata.create_all(engine)
            self.client = self.pdi.get(FlaskAppWrapper).test_client()
        except Exception:
            self.tearDown()
            raise

    def tearDown(self):
        if hasattr(self, "pdi") and self.pdi is not None:
            self.pdi.cleanup()
            del self.pdi
        # SQLite file is written next to main.py; remove it so reruns
        # start from an empty schema.
        db_path = os.path.join(_EXAMPLE_ROOT, "notes.db")
        if os.path.exists(db_path):
            os.remove(db_path)
        htmlcov_like = os.path.join(_EXAMPLE_ROOT, "__pycache__")
        if os.path.isdir(htmlcov_like):
            shutil.rmtree(htmlcov_like, ignore_errors=True)
        return super().tearDown()

    def test_create_then_list_returns_the_persisted_note(self):
        # Arrange
        payload = {"Title": "Buy milk", "Body": "2 %"}

        # Act — create
        create_resp = self.client.post(
            "api/Application/Notes",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(create_resp.status_code, 200)
        create_body = json.loads(create_resp.get_data(as_text=True))
        self.assertTrue(create_body["IsSuccess"])

        # Act — list
        list_resp = self.client.get("api/Application/Notes")
        self.assertEqual(list_resp.status_code, 200)
        list_body = json.loads(list_resp.get_data(as_text=True))
        self.assertTrue(list_body["IsSuccess"])

        # Assert — the note we just created came back
        notes = list_body["Result"]["Data"]
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["Title"], "Buy milk")
        self.assertEqual(notes[0]["Body"], "2 %")
        self.assertIsNotNone(notes[0]["Id"])
        self.assertIsNotNone(notes[0]["CreateUserTime"])
