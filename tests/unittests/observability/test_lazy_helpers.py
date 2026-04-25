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
