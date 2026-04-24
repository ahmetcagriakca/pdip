"""Unit tests for the ``Pdi`` entry point.

``Pdi`` wraps the ``DependencyContainer`` and is the single bootstrap
seam consumers import. These tests pin down:

* that construction installs a ``DependencyContainer.Instance``,
* that ``cleanup`` tears it back down,
* that ``get`` delegates to the service provider,
* that auto-discovered root directory resolves to the caller's
  location (used when ``Pdi()`` is called with no argument).
"""

import os
import tempfile
from unittest import TestCase
from unittest.mock import patch

from pdip.base import Pdi
from pdip.dependency.container import DependencyContainer


class PdiLifecycle(TestCase):
    def setUp(self):
        DependencyContainer.cleanup()
        self._tmp = tempfile.mkdtemp(prefix="pdip-test-")

    def tearDown(self):
        DependencyContainer.cleanup()
        # best-effort cleanup of the empty temp directory
        try:
            os.rmdir(self._tmp)
        except OSError:
            pass

    def test_construction_installs_dependency_container_instance(self):
        pdi = Pdi(root_directory=self._tmp)
        try:
            self.assertIsNotNone(DependencyContainer.Instance)
        finally:
            pdi.cleanup()

    def test_cleanup_removes_dependency_container_instance(self):
        pdi = Pdi(root_directory=self._tmp)
        pdi.cleanup()
        self.assertIsNone(DependencyContainer.Instance)


class PdiGetDelegatesToProvider(TestCase):
    def setUp(self):
        DependencyContainer.cleanup()
        self._tmp = tempfile.mkdtemp(prefix="pdip-test-")
        self.pdi = Pdi(root_directory=self._tmp)

    def tearDown(self):
        self.pdi.cleanup()
        try:
            os.rmdir(self._tmp)
        except OSError:
            pass

    def test_get_returns_value_from_service_provider(self):
        sentinel = object()
        with patch.object(
            DependencyContainer.Instance, "get", return_value=sentinel
        ) as provider_get:
            result = self.pdi.get(str)

        self.assertIs(result, sentinel)
        provider_get.assert_called_once_with(str)


class PdiAutoDiscoversRootDirectory(TestCase):
    """When ``root_directory`` is omitted, ``Pdi`` walks the call stack to
    derive the caller's directory. Verify it produces *a* valid path and
    does not crash."""

    def tearDown(self):
        DependencyContainer.cleanup()

    def test_default_root_directory_is_a_real_directory(self):
        pdi = Pdi()
        try:
            self.assertTrue(os.path.isdir(pdi.root_directory))
        finally:
            pdi.cleanup()
