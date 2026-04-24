"""Unit tests for ``pdip.dependency.container.DependencyContainer``.

The container wraps a ``ServiceProvider`` on the class and exposes
``initialize_service`` / ``cleanup`` for bootstrap. These tests cover
the failure path of ``initialize_service`` (where a raising
``ServiceProvider`` must trigger ``cleanup`` and re-raise) and the
cleanup of an already-missing instance.
"""

from unittest import TestCase
from unittest.mock import patch

from pdip.dependency.container import DependencyContainer


class DependencyContainerInitializeFailurePath(TestCase):
    def setUp(self):
        DependencyContainer.cleanup()

    def tearDown(self):
        DependencyContainer.cleanup()

    def test_service_provider_construction_failure_triggers_cleanup_and_reraises(self):
        # Arrange — patch ``ServiceProvider`` inside the module under
        # test so construction fails immediately.
        with patch(
            "pdip.dependency.container.dependency_container.ServiceProvider",
            side_effect=RuntimeError("boom"),
        ):
            # Act / Assert — the original exception is re-raised.
            with self.assertRaises(RuntimeError) as ctx:
                DependencyContainer.initialize_service(root_directory="/tmp")

        self.assertEqual(str(ctx.exception), "boom")
        # And ``cleanup`` ran: the Instance is None after the failure.
        self.assertIsNone(DependencyContainer.Instance)


class DependencyContainerCleanupIsIdempotent(TestCase):
    def setUp(self):
        DependencyContainer.cleanup()

    def test_cleanup_with_no_instance_is_a_no_op(self):
        # Arrange: Instance is already None after setUp.
        self.assertIsNone(DependencyContainer.Instance)

        # Act — must not raise.
        DependencyContainer.cleanup()

        # Assert — still None.
        self.assertIsNone(DependencyContainer.Instance)
