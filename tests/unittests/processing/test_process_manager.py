from unittest import TestCase
from unittest.mock import MagicMock, patch

from pdip.logging.loggers.console import ConsoleLogger
from pdip.processing import ProcessManager


class TestProcessManager(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        return super().tearDown()

    @classmethod
    def process_method(cls, sub_process_id, data):
        print(f"{sub_process_id}-{data}")
        return data

    def test_process(self):
        process_manager = ProcessManager(logger=ConsoleLogger())
        test_data = 1
        data_kwargs = {
            "data": test_data
        }

        process_manager.start_processes(
            process_count=2,
            target_method=self.process_method,
            kwargs=data_kwargs)
        results = process_manager.get_results()
        assert len(results) == 2
        for result in results:
            assert result.State == 3 and result.Result == test_data

    @classmethod
    def process_error_method(cls, sub_process_id, data):

        print(f"{sub_process_id}-{data}")
        raise Exception("process has error")
        return data

    def test_process_error(self):
        process_manager = ProcessManager(logger=ConsoleLogger())
        test_data = 1
        data_kwargs = {
            "data": test_data
        }

        process_manager.start_processes(
            process_count=2,
            target_method=self.process_error_method,
            kwargs=data_kwargs)
        results = process_manager.get_results()
        assert len(results) == 2
        errored = [r for r in results if r.State == 4]
        assert errored, 'expected at least one subprocess to report State=4'
        for result in errored:
            assert str(result.Exception) == 'process has error'


class ProcessManagerInjectsTraceCarrierIntoKwargs(TestCase):
    """ADR-0033 §3 — ``start_processes`` must inject the W3C trace
    carrier into the kwargs payload that crosses the process boundary
    so the worker can rejoin the parent's span. The injection is
    delegated to ``pdip.observability.inject_context`` so the
    behaviour gated by ``PDIP_OBSERVABILITY_ENABLED`` flows through
    transparently.
    """

    def test_carrier_added_when_inject_returns_a_dict(self):
        # Arrange — short-circuit the multiprocessing plumbing so we
        # can assert kwargs without spawning a child. ``__start_process``
        # is what enqueues the kwargs onto the cross-process queue.
        captured_kwargs = []

        def _capture(self_, sub_process_id, process_queue,
                     process_result_queue, target_method, kwargs):
            captured_kwargs.append(dict(kwargs))
            return MagicMock(name="process")

        process_manager = ProcessManager(logger=MagicMock(name="logger"))
        carrier_sentinel = {"traceparent": "00-abcd-ef01-01"}
        with patch(
            "pdip.processing.base.process_manager.inject_context",
            return_value=carrier_sentinel,
        ), patch.object(
            ProcessManager, "_ProcessManager__start_process", _capture
        ), patch.object(
            ProcessManager, "create_queue", return_value=MagicMock()
        ):
            process_manager.start_processes(
                target_method=lambda **_: None,
                kwargs={"data": 1},
                process_count=1,
            )

        # Act / Assert — the kwargs that reached the subprocess
        # contains both the user payload and the framework-private
        # carrier key.
        self.assertEqual(len(captured_kwargs), 1)
        self.assertEqual(captured_kwargs[0]["data"], 1)
        self.assertEqual(
            captured_kwargs[0]["_pdip_trace_carrier"], carrier_sentinel
        )

    def test_no_carrier_added_when_inject_returns_none(self):
        captured_kwargs = []

        def _capture(self_, sub_process_id, process_queue,
                     process_result_queue, target_method, kwargs):
            captured_kwargs.append(dict(kwargs))
            return MagicMock(name="process")

        process_manager = ProcessManager(logger=MagicMock(name="logger"))
        with patch(
            "pdip.processing.base.process_manager.inject_context",
            return_value=None,
        ), patch.object(
            ProcessManager, "_ProcessManager__start_process", _capture
        ), patch.object(
            ProcessManager, "create_queue", return_value=MagicMock()
        ):
            process_manager.start_processes(
                target_method=lambda **_: None,
                kwargs={"data": 2},
                process_count=1,
            )

        # When no active span / observability disabled, kwargs is
        # unchanged — the framework-private key is absent.
        self.assertEqual(len(captured_kwargs), 1)
        self.assertEqual(captured_kwargs[0], {"data": 2})

    def test_caller_kwargs_dict_is_not_mutated(self):
        # The injection must not mutate the dict the caller passed
        # in — that would leak the carrier into subsequent calls.
        captured_kwargs = []

        def _capture(self_, sub_process_id, process_queue,
                     process_result_queue, target_method, kwargs):
            captured_kwargs.append(dict(kwargs))
            return MagicMock(name="process")

        process_manager = ProcessManager(logger=MagicMock(name="logger"))
        original_kwargs = {"data": 3}
        with patch(
            "pdip.processing.base.process_manager.inject_context",
            return_value={"traceparent": "00-x"},
        ), patch.object(
            ProcessManager, "_ProcessManager__start_process", _capture
        ), patch.object(
            ProcessManager, "create_queue", return_value=MagicMock()
        ):
            process_manager.start_processes(
                target_method=lambda **_: None,
                kwargs=original_kwargs,
                process_count=1,
            )

        self.assertNotIn("_pdip_trace_carrier", original_kwargs)
        self.assertIn("_pdip_trace_carrier", captured_kwargs[0])
