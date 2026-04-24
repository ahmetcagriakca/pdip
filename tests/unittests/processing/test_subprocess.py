"""Unit tests for ``pdip.processing.base.subprocess.Subprocess``.

The ``Subprocess`` worker is what the ``ProcessManager`` spawns in a
child process; ``start(...)`` pulls ``ProcessTask`` items off the
input queue, runs ``target_method(**kwargs)`` for live tasks, and
feeds the result (or exception) back on the result queue.

These tests exercise ``start`` directly in-process — no real child
process — using plain ``queue.Queue`` instances and a callable
target. ADR-0026 D.2 forbids real subprocesses in unit tests; the
``ProcessManager`` happy-path suite covers the spawn-level behaviour.
"""

from queue import Queue
from unittest import TestCase
from unittest.mock import MagicMock, patch

from pdip.processing.base.subprocess import Subprocess
from pdip.processing.models import ProcessTask


def _build_subject():
    """Construct a ``Subprocess`` with the in-process ``ConsoleLogger``
    fallback (``initialize_container=None``), then swap the logger for
    a mock so we can observe info/error calls without touching real
    stdout."""
    subject = Subprocess()
    subject.logger = MagicMock(name="logger")
    return subject


def _start_with(subject, tasks, target, kwargs=None, sub_process_id=7):
    """Wire an input queue pre-loaded with ``tasks``, run ``start``,
    and return the result queue so the caller can drain it."""
    in_q = Queue()
    out_q = Queue()
    for t in tasks:
        in_q.put(t)
    subject.start(
        sub_process_id=sub_process_id,
        process_queue=in_q,
        process_result_queue=out_q,
        target_method=target,
        kwargs=kwargs if kwargs is not None else {},
    )
    return out_q


def _drain(q):
    out = []
    while not q.empty():
        out.append(q.get_nowait())
    return out


class SubprocessProcessesLiveTask(TestCase):
    def test_start_runs_target_and_publishes_finished_task(self):
        subject = _build_subject()
        target = MagicMock(name="target", return_value="payload")
        live = ProcessTask(SubProcessId=None, IsFinished=False)

        out = _start_with(subject, [live], target, kwargs={"data": 1})

        results = _drain(out)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].IsFinished)
        self.assertEqual(results[0].State, 3)
        self.assertEqual(results[0].Result, "payload")

    def test_start_stamps_sub_process_id_on_the_task(self):
        subject = _build_subject()
        target = MagicMock(return_value=None)
        live = ProcessTask(IsFinished=False)

        out = _start_with(subject, [live], target, sub_process_id=11)

        task = _drain(out)[0]
        self.assertEqual(task.SubProcessId, 11)

    def test_start_passes_sub_process_id_into_target_kwargs(self):
        subject = _build_subject()
        target = MagicMock(return_value="ok")
        live = ProcessTask(IsFinished=False)

        _start_with(subject, [live], target, kwargs={"data": "x"},
                    sub_process_id=5)

        target.assert_called_once_with(sub_process_id=5, data="x")


class SubprocessHandlesFinishSignal(TestCase):
    def test_start_returns_without_calling_target_when_first_task_is_finished(self):
        subject = _build_subject()
        target = MagicMock(name="target")
        finished = ProcessTask(IsFinished=True)
        out_q = Queue()
        in_q = Queue()
        in_q.put(finished)

        subject.start(
            sub_process_id=3,
            process_queue=in_q,
            process_result_queue=out_q,
            target_method=target,
            kwargs={},
        )

        target.assert_not_called()
        self.assertTrue(out_q.empty())

    def test_start_logs_finished_message_on_finish_signal(self):
        subject = _build_subject()
        finished = ProcessTask(IsFinished=True)

        _start_with(subject, [finished], MagicMock())

        # Two info calls: startup banner + finish banner.
        messages = [call.args[0] for call in subject.logger.info.call_args_list]
        self.assertTrue(any("process finished" in m for m in messages))


class SubprocessReportsTargetExceptions(TestCase):
    def test_start_puts_error_task_when_target_raises(self):
        subject = _build_subject()
        boom = RuntimeError("explode")

        def target(**_):
            raise boom

        live = ProcessTask(IsFinished=False)

        out = _start_with(subject, [live], target, sub_process_id=9)

        results = _drain(out)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].State, 4)
        self.assertTrue(results[0].IsFinished)
        self.assertIs(results[0].Exception, boom)
        self.assertEqual(results[0].SubProcessId, 9)

    def test_start_captures_traceback_string_on_error(self):
        subject = _build_subject()

        def target(**_):
            raise ValueError("bad")

        live = ProcessTask(IsFinished=False)

        out = _start_with(subject, [live], target)

        task = _drain(out)[0]
        self.assertIsInstance(task.Traceback, str)
        self.assertIn("ValueError", task.Traceback)

    def test_start_logs_error_when_target_raises(self):
        subject = _build_subject()

        def target(**_):
            raise RuntimeError("fail")

        live = ProcessTask(IsFinished=False)

        _start_with(subject, [live], target)

        subject.logger.error.assert_called_once()


class SubprocessInitSelectsLoggerByContainerFlag(TestCase):
    def test_init_falls_back_to_console_logger_without_container(self):
        # ``initialize_container`` left as ``None`` exercises the else
        # branch: we must not touch the DI container.
        from pdip.logging.loggers.console import ConsoleLogger

        subject = Subprocess()

        self.assertIsInstance(subject.logger, ConsoleLogger)

    def test_init_boots_container_and_resolves_logger_when_flag_set(self):
        # ``initialize_container=True`` must call into
        # ``DependencyContainer.initialize_service`` and then resolve a
        # logger from the container. Unit tests never boot a real Pdi,
        # so we patch the container at the module boundary.
        from pdip.logging.loggers.console import ConsoleLogger

        resolved_logger = MagicMock(name="resolved_logger")
        fake_instance = MagicMock(name="service_provider")
        fake_instance.get.return_value = resolved_logger

        with patch(
            "pdip.processing.base.subprocess.DependencyContainer"
        ) as container:
            container.Instance = fake_instance

            subject = Subprocess(
                initialize_container=True, root_directory="/tmp/fake-root"
            )

        container.initialize_service.assert_called_once_with(
            root_directory="/tmp/fake-root", initialize_flask=False
        )
        fake_instance.get.assert_called_once_with(ConsoleLogger)
        self.assertIs(subject.logger, resolved_logger)
