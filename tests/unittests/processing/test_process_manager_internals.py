"""Unit tests for ``ProcessManager`` internals that can't be reached
through the happy-path spawn tests in ``test_process_manager.py``.

The following branches need explicit coverage:

* The ``DependencyContainer.Instance``-is-set branch in
  ``__start_process``: the parent process passes the container's
  root directory and flips ``initialize_container=True``.
* ``start_subprocess`` static helper: constructs a ``Subprocess`` and
  forwards the call. We keep this in-process by patching
  ``Subprocess``.
* ``__check_unfinished_processes`` marks non-alive processes as
  finished, so the dispatch loop can exit cleanly.

No real children are spawned; every collaborator (``_MP_CONTEXT``,
``Subprocess``, ``DependencyContainer``) is patched at the boundary.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from pdip.processing import ProcessManager
from pdip.processing.models import ProcessInfo


class ProcessManagerStartPropagatesContainerState(TestCase):
    def test_start_process_uses_container_root_when_instance_set(self):
        manager = ProcessManager(logger=MagicMock(name="logger"))
        fake_process = MagicMock(name="spawned_process")
        fake_container_instance = MagicMock(name="service_provider")
        fake_container_instance.root_directory = "/opt/pdip"

        with patch(
            "pdip.processing.base.process_manager._MP_CONTEXT"
        ) as mp_ctx, patch(
            "pdip.processing.base.process_manager.DependencyContainer"
        ) as container:
            mp_ctx.Process.return_value = fake_process
            mp_ctx.Manager.return_value = MagicMock(
                Queue=lambda: MagicMock(name="queue")
            )
            container.Instance = fake_container_instance

            manager.start_processes(
                target_method=lambda **_: None,
                kwargs={"data": 1},
                process_count=1,
            )

        # The parent-side args tuple to Process(...) must include the
        # container's root_directory and initialize_container=True.
        args_tuple = mp_ctx.Process.call_args.kwargs["args"]
        self.assertEqual(args_tuple[1], "/opt/pdip")  # root_directory
        self.assertTrue(args_tuple[2])  # initialize_container flag

    def test_start_process_defaults_to_none_root_when_instance_absent(self):
        manager = ProcessManager(logger=MagicMock(name="logger"))
        fake_process = MagicMock(name="spawned_process")

        with patch(
            "pdip.processing.base.process_manager._MP_CONTEXT"
        ) as mp_ctx, patch(
            "pdip.processing.base.process_manager.DependencyContainer"
        ) as container:
            mp_ctx.Process.return_value = fake_process
            mp_ctx.Manager.return_value = MagicMock(
                Queue=lambda: MagicMock(name="queue")
            )
            container.Instance = None

            manager.start_processes(
                target_method=lambda **_: None,
                kwargs={"data": 1},
                process_count=1,
            )

        args_tuple = mp_ctx.Process.call_args.kwargs["args"]
        self.assertIsNone(args_tuple[1])
        self.assertFalse(args_tuple[2])


class ProcessManagerStartSubprocessDelegates(TestCase):
    def test_start_subprocess_constructs_subprocess_and_forwards_call(self):
        with patch(
            "pdip.processing.base.process_manager.Subprocess"
        ) as subprocess_cls:
            in_q = MagicMock(name="in_q")
            out_q = MagicMock(name="out_q")
            target = MagicMock(name="target")

            ProcessManager.start_subprocess(
                sub_process_id=5,
                root_directory="/root",
                initialize_container=True,
                process_queue=in_q,
                process_result_queue=out_q,
                target_method=target,
                kwargs={"data": "payload"},
            )

        subprocess_cls.assert_called_once_with(
            root_directory="/root", initialize_container=True
        )
        subprocess_cls.return_value.start.assert_called_once_with(
            sub_process_id=5,
            process_queue=in_q,
            process_result_queue=out_q,
            target_method=target,
            kwargs={"data": "payload"},
        )


class ProcessManagerFlagsUnfinishedDeadProcesses(TestCase):
    def test_dead_process_is_marked_finished_so_the_loop_can_exit(self):
        manager = ProcessManager(logger=MagicMock(name="logger"))
        dead = MagicMock(name="dead_process")
        dead.is_alive.return_value = False
        alive = MagicMock(name="alive_process")
        alive.is_alive.return_value = True

        manager._processes = [
            ProcessInfo(Process=dead, SubProcessId=1, IsFinished=False),
            ProcessInfo(Process=alive, SubProcessId=2, IsFinished=False),
        ]

        # private name-mangled access is the only way to exercise this
        # helper in isolation.
        manager._ProcessManager__check_unfinished_processes()

        self.assertTrue(manager._processes[0].IsFinished)
        self.assertFalse(manager._processes[1].IsFinished)
        manager.logger.info.assert_called_once()
        self.assertIn(
            "Unfinished process found",
            manager.logger.info.call_args.args[0],
        )
