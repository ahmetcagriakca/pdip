"""Unit tests for ``pdip.observability`` lazy helpers (ADR-0033).

The helpers must be:

- No-op by default (``PDIP_OBSERVABILITY_ENABLED`` unset or ``"0"``)
  so that installing pdip never starts emitting telemetry.
- Lazy with respect to ``opentelemetry`` — never imported at
  module load, only when emission is actually requested.
- Resilient: if the env toggle is on but the ``opentelemetry``
  packages are not installed, fall back to the no-op tracer /
  meter rather than crashing the host application.

The OTel-path tests inject a fake ``opentelemetry`` package into
``sys.modules`` so they exercise the real import branch without
requiring the dependency to be installed.
"""

import os
import sys
import types
from unittest import TestCase
from unittest.mock import MagicMock

from pdip.observability import get_meter, get_tracer
from pdip.observability._lazy import (
    PDIP_OBSERVABILITY_ENV,
    inject_context,
    use_context,
)


# ---------------------------------------------------------------------------
# Helpers — env / sys.modules manipulation common to multiple cases.
# ---------------------------------------------------------------------------


def _enable_observability():
    os.environ[PDIP_OBSERVABILITY_ENV] = "1"


def _clear_observability_env():
    os.environ.pop(PDIP_OBSERVABILITY_ENV, None)


def _install_fake_opentelemetry():
    """Inject a minimal fake ``opentelemetry.trace`` and
    ``opentelemetry.metrics`` into ``sys.modules`` and return the
    handles the tests assert against."""
    fake_trace = MagicMock(name="opentelemetry.trace")
    fake_metrics = MagicMock(name="opentelemetry.metrics")
    fake_pkg = types.ModuleType("opentelemetry")
    fake_pkg.trace = fake_trace
    fake_pkg.metrics = fake_metrics
    sys.modules["opentelemetry"] = fake_pkg
    sys.modules["opentelemetry.trace"] = fake_trace
    sys.modules["opentelemetry.metrics"] = fake_metrics
    return fake_trace, fake_metrics


def _uninstall_fake_opentelemetry():
    for name in (
        "opentelemetry",
        "opentelemetry.trace",
        "opentelemetry.metrics",
    ):
        sys.modules.pop(name, None)


# ---------------------------------------------------------------------------
# No-op behaviour when observability is disabled.
# ---------------------------------------------------------------------------


class NoOpTracerWhenObservabilityDisabled(TestCase):
    def setUp(self):
        _clear_observability_env()

    def test_get_tracer_returns_a_no_op_when_env_unset(self):
        tracer = get_tracer("pdip.cqrs")

        # The no-op span is yielded as the context-manager value;
        # asserting we can enter and exit without raising is the
        # whole point.
        with tracer.start_as_current_span("pdip.cqrs.command") as span:
            self.assertIsNotNone(span)

    def test_no_op_span_accepts_set_attribute_set_status_record_exception(self):
        tracer = get_tracer("pdip.cqrs")
        with tracer.start_as_current_span("pdip.cqrs.command") as span:
            # All three calls must return ``None`` and never raise —
            # the tracer is allowed to be called from real code paths
            # exactly the same way as the OTel SDK tracer.
            self.assertIsNone(span.set_attribute("pdip.cqrs.handler", "X"))
            self.assertIsNone(span.set_status("ok"))
            self.assertIsNone(span.record_exception(RuntimeError("x")))


class NoOpMeterWhenObservabilityDisabled(TestCase):
    def setUp(self):
        _clear_observability_env()

    def test_get_meter_returns_a_no_op_when_env_unset(self):
        meter = get_meter("pdip.cqrs")

        counter = meter.create_counter("pdip.cqrs.dispatch.count")
        histogram = meter.create_histogram("pdip.cqrs.dispatch.duration")
        up_down = meter.create_up_down_counter("pdip.pubsub.queue.depth")

        # Every emission API on the no-op instrument must accept a
        # value + optional attributes and silently return ``None``.
        self.assertIsNone(counter.add(1, {"pdip.cqrs.kind": "command"}))
        self.assertIsNone(histogram.record(0.5))
        self.assertIsNone(up_down.add(-1))


class NoOpWhenEnvSetExplicitlyToZero(TestCase):
    def setUp(self):
        os.environ[PDIP_OBSERVABILITY_ENV] = "0"

    def tearDown(self):
        _clear_observability_env()

    def test_explicit_zero_is_treated_as_disabled(self):
        # ADR-0033 §6 says the toggle defaults to "0"; an explicit "0"
        # must behave the same as an absent variable.
        tracer = get_tracer("pdip.cqrs")
        with tracer.start_as_current_span("x") as span:
            # The fact that we reach here without raising and that
            # ``span`` exposes the no-op surface is the assertion.
            self.assertTrue(hasattr(span, "set_attribute"))


# ---------------------------------------------------------------------------
# OTel path when observability is enabled and ``opentelemetry`` is
# importable.
# ---------------------------------------------------------------------------


class OTelTracerWhenObservabilityEnabled(TestCase):
    def setUp(self):
        _enable_observability()
        self.fake_trace, self.fake_metrics = _install_fake_opentelemetry()

    def tearDown(self):
        _uninstall_fake_opentelemetry()
        _clear_observability_env()

    def test_get_tracer_delegates_to_opentelemetry_trace_get_tracer(self):
        result = get_tracer("pdip.cqrs")

        self.fake_trace.get_tracer.assert_called_once_with("pdip.cqrs")
        self.assertIs(result, self.fake_trace.get_tracer.return_value)

    def test_get_meter_delegates_to_opentelemetry_metrics_get_meter(self):
        result = get_meter("pdip.integrator")

        self.fake_metrics.get_meter.assert_called_once_with("pdip.integrator")
        self.assertIs(result, self.fake_metrics.get_meter.return_value)


# ---------------------------------------------------------------------------
# OTel path when observability is enabled but ``opentelemetry`` is
# NOT importable. ADR-0033 §2 requires we fall back to the no-op
# rather than crashing the host application.
# ---------------------------------------------------------------------------


class FallsBackToNoOpWhenOpenTelemetryMissing(TestCase):
    def setUp(self):
        _enable_observability()
        # Ensure ``opentelemetry`` cannot be imported even if the
        # package happens to be installed in the test environment:
        # poison the entries in ``sys.modules`` and block further
        # discovery via a meta_path finder.
        self._saved = {}
        for name in (
            "opentelemetry",
            "opentelemetry.trace",
            "opentelemetry.metrics",
        ):
            if name in sys.modules:
                self._saved[name] = sys.modules[name]
            sys.modules[name] = None  # ImportError on ``import``

    def tearDown(self):
        for name in (
            "opentelemetry",
            "opentelemetry.trace",
            "opentelemetry.metrics",
        ):
            sys.modules.pop(name, None)
            if name in self._saved:
                sys.modules[name] = self._saved[name]
        _clear_observability_env()

    def test_get_tracer_returns_no_op_when_opentelemetry_unavailable(self):
        tracer = get_tracer("pdip.cqrs")
        with tracer.start_as_current_span("pdip.cqrs.command") as span:
            # Fall-through to no-op span; the call must not raise
            # ``ImportError`` and must yield a span-shaped object.
            self.assertTrue(hasattr(span, "set_attribute"))

    def test_get_meter_returns_no_op_when_opentelemetry_unavailable(self):
        meter = get_meter("pdip.cqrs")
        counter = meter.create_counter("pdip.cqrs.dispatch.count")
        # ``add`` on the no-op instrument must accept the OTel calling
        # convention and return ``None``.
        self.assertIsNone(counter.add(1))


# ---------------------------------------------------------------------------
# Cross-process context propagation (ADR-0033 §3, §6).
#
# ``inject_context`` produces a W3C-compatible carrier dict that
# ``ProcessManager`` ships across the process boundary; ``use_context``
# is the matching context-manager that the worker uses to attach the
# extracted span context for the duration of the task. Both must be
# silent no-ops when observability is disabled or OpenTelemetry is
# missing — the propagation contract never crashes the host.
# ---------------------------------------------------------------------------


def _install_fake_propagate(propagate_inject_carrier=None):
    """Inject a fake ``opentelemetry.propagate`` (and ``context``)
    into ``sys.modules`` so the helpers' lazy import resolves
    deterministically. Returns the fakes for assertion."""
    fake_propagate = MagicMock(name="opentelemetry.propagate")
    if propagate_inject_carrier is not None:
        # propagate.inject mutates the carrier in place.
        def _inject(carrier, *_, **__):
            carrier.update(propagate_inject_carrier)
        fake_propagate.inject.side_effect = _inject
    fake_context = MagicMock(name="opentelemetry.context")
    fake_pkg = types.ModuleType("opentelemetry")
    fake_pkg.propagate = fake_propagate
    fake_pkg.context = fake_context
    sys.modules["opentelemetry"] = fake_pkg
    sys.modules["opentelemetry.propagate"] = fake_propagate
    sys.modules["opentelemetry.context"] = fake_context
    return fake_propagate, fake_context


def _uninstall_fake_propagate():
    for name in (
        "opentelemetry",
        "opentelemetry.propagate",
        "opentelemetry.context",
    ):
        sys.modules.pop(name, None)


class InjectContextNoOpWhenDisabled(TestCase):
    def setUp(self):
        _clear_observability_env()

    def test_returns_none_when_observability_disabled(self):
        # No carrier when observability is off; callers feed ``None``
        # straight into kwargs without ceremony.
        self.assertIsNone(inject_context())


class InjectContextProducesCarrierWhenEnabled(TestCase):
    def setUp(self):
        _enable_observability()
        self._fake_propagate, _ = _install_fake_propagate(
            propagate_inject_carrier={"traceparent": "00-abcd-ef01-01"}
        )

    def tearDown(self):
        _uninstall_fake_propagate()
        _clear_observability_env()

    def test_returns_carrier_dict_populated_by_propagate_inject(self):
        result = inject_context()

        self.assertEqual(result, {"traceparent": "00-abcd-ef01-01"})
        self._fake_propagate.inject.assert_called_once()

    def test_returns_none_when_no_active_context(self):
        # If propagate.inject leaves the carrier empty (no active
        # span), the helper must return ``None`` so callers can use
        # the standard ``if carrier is not None`` idiom.
        self._fake_propagate.inject.side_effect = lambda carrier, *_, **__: None

        self.assertIsNone(inject_context())


class InjectContextFallsBackToNoneWhenOpenTelemetryMissing(TestCase):
    def setUp(self):
        _enable_observability()
        self._saved = {}
        for name in ("opentelemetry", "opentelemetry.propagate"):
            if name in sys.modules:
                self._saved[name] = sys.modules[name]
            sys.modules[name] = None

    def tearDown(self):
        for name in ("opentelemetry", "opentelemetry.propagate"):
            sys.modules.pop(name, None)
            if name in self._saved:
                sys.modules[name] = self._saved[name]
        _clear_observability_env()

    def test_returns_none_when_opentelemetry_unavailable(self):
        self.assertIsNone(inject_context())


class UseContextNoOpWhenDisabled(TestCase):
    def setUp(self):
        _clear_observability_env()

    def test_use_context_with_disabled_observability_yields_quietly(self):
        # The ``with`` block must still execute its body and never
        # raise — that is the entire contract on the no-op path.
        marker = []
        with use_context({"traceparent": "ignored"}):
            marker.append("body-ran")

        self.assertEqual(marker, ["body-ran"])

    def test_use_context_with_falsy_carrier_yields_quietly(self):
        marker = []
        with use_context(None):
            marker.append("ran")
        self.assertEqual(marker, ["ran"])


class UseContextAttachesAndDetachesWhenEnabled(TestCase):
    def setUp(self):
        _enable_observability()
        self._fake_propagate, self._fake_context = _install_fake_propagate()
        self._fake_propagate.extract.return_value = "extracted-ctx"
        self._fake_context.attach.return_value = "attach-token"

    def tearDown(self):
        _uninstall_fake_propagate()
        _clear_observability_env()

    def test_extract_attach_and_detach_are_called_in_order(self):
        with use_context({"traceparent": "00-abcd"}):
            # Inside the body the context must already be attached.
            self._fake_propagate.extract.assert_called_once_with(
                {"traceparent": "00-abcd"}
            )
            self._fake_context.attach.assert_called_once_with("extracted-ctx")
            # ``detach`` MUST NOT have run yet — that would defeat
            # the purpose of the context manager.
            self._fake_context.detach.assert_not_called()

        self._fake_context.detach.assert_called_once_with("attach-token")

    def test_detach_runs_even_when_body_raises(self):
        with self.assertRaises(RuntimeError):
            with use_context({"traceparent": "00-abcd"}):
                raise RuntimeError("boom")

        self._fake_context.detach.assert_called_once_with("attach-token")


class UseContextFallsBackToNoOpWhenOpenTelemetryMissing(TestCase):
    def setUp(self):
        _enable_observability()
        self._saved = {}
        for name in (
            "opentelemetry",
            "opentelemetry.propagate",
            "opentelemetry.context",
        ):
            if name in sys.modules:
                self._saved[name] = sys.modules[name]
            sys.modules[name] = None

    def tearDown(self):
        for name in (
            "opentelemetry",
            "opentelemetry.propagate",
            "opentelemetry.context",
        ):
            sys.modules.pop(name, None)
            if name in self._saved:
                sys.modules[name] = self._saved[name]
        _clear_observability_env()

    def test_yields_quietly_when_opentelemetry_unavailable(self):
        marker = []
        with use_context({"traceparent": "00-abcd"}):
            marker.append("ran")
        self.assertEqual(marker, ["ran"])
