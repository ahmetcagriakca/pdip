"""Coverage gate for ``examples/etl``.

Mirrors the ``tests/unittests/examples/crud_api/test_crud_api_example.py``
pattern: import the runnable example and exercise its public flow
against a temp directory so any framework change that breaks the
example surfaces in the unit-test matrix instead of when the next
contributor tries to run it locally.
"""

import os
import tempfile
from unittest import TestCase

from examples.etl.main import run


class TestEtlExample(TestCase):
    def setUp(self):
        self._workdir = tempfile.mkdtemp(prefix="pdip-etl-example-test-")
        self._source = os.path.join(self._workdir, "source.db")
        self._target = os.path.join(self._workdir, "target.db")

    def test_run_copies_three_seeded_rows_into_target(self):
        rows = run(source_path=self._source, target_path=self._target)

        self.assertEqual(len(rows), 3)
        self.assertEqual([r["id"] for r in rows], [1, 2, 3])
        self.assertEqual(
            [r["name"] for r in rows],
            ["Ada Lovelace", "Alan Turing", "Grace Hopper"],
        )

    def test_run_is_idempotent_on_repeated_invocation(self):
        # Truncate-then-reload semantics inside ``run`` mean a second
        # invocation against the same files lands the same three
        # rows, not six.
        run(source_path=self._source, target_path=self._target)
        rows = run(source_path=self._source, target_path=self._target)

        self.assertEqual(len(rows), 3)
