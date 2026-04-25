"""Lazy, no-op-by-default OpenTelemetry helpers (ADR-0033).

The framework calls :func:`get_tracer` and :func:`get_meter` from
instrumented sites (e.g. the CQRS dispatcher, the integrator). When
``PDIP_OBSERVABILITY_ENABLED`` is unset or ``"0"``, both helpers
return no-op objects whose API matches the OTel surface enough that
calling code does not need any conditional logic.

When the toggle is on, the helpers import ``opentelemetry`` lazily
and delegate to the registered global tracer / meter provider. If
``opentelemetry`` is not installed (the ``pdip[observability]`` extra
was not selected) the helpers fall back to the no-op path rather than
crashing the host application — see ADR-0033 §2.
"""

import os
from contextlib import contextmanager


PDIP_OBSERVABILITY_ENV = "PDIP_OBSERVABILITY_ENABLED"


def _observability_enabled():
    return os.environ.get(PDIP_OBSERVABILITY_ENV, "0") == "1"


class _NoOpSpan:
    """Span-shaped object whose mutators are silently ignored."""

    def set_attribute(self, key, value):
        return None

    def set_status(self, status):
        return None

    def record_exception(self, exception):
        return None


class _NoOpTracer:
    @contextmanager
    def start_as_current_span(self, name):
        yield _NoOpSpan()


class _NoOpInstrument:
    """Counter / histogram / up-down-counter shape (``add`` + ``record``)."""

    def add(self, amount, attributes=None):
        return None

    def record(self, amount, attributes=None):
        return None


class _NoOpMeter:
    def create_counter(self, name, unit=None, description=None):
        return _NoOpInstrument()

    def create_histogram(self, name, unit=None, description=None):
        return _NoOpInstrument()

    def create_up_down_counter(self, name, unit=None, description=None):
        return _NoOpInstrument()


_NOOP_TRACER = _NoOpTracer()
_NOOP_METER = _NoOpMeter()


def get_tracer(name):
    """Return a tracer for ``name``.

    No-op when observability is disabled or when ``opentelemetry`` is
    not installed; delegates to ``opentelemetry.trace.get_tracer``
    otherwise.
    """
    if not _observability_enabled():
        return _NOOP_TRACER
    try:
        from opentelemetry import trace
    except ImportError:
        return _NOOP_TRACER
    return trace.get_tracer(name)


def get_meter(name):
    """Return a meter for ``name``.

    No-op when observability is disabled or when ``opentelemetry`` is
    not installed; delegates to ``opentelemetry.metrics.get_meter``
    otherwise.
    """
    if not _observability_enabled():
        return _NOOP_METER
    try:
        from opentelemetry import metrics
    except ImportError:
        return _NOOP_METER
    return metrics.get_meter(name)


def inject_context():
    """Return a W3C-compatible carrier dict for the current span
    context, or ``None`` when observability is disabled, OpenTelemetry
    is unavailable, or no context is active.

    The carrier is the picklable payload that ``ProcessManager`` ships
    across the process boundary so a child process can rejoin the
    parent's trace (ADR-0033 §3 cross-process span propagation).
    """
    if not _observability_enabled():
        return None
    try:
        from opentelemetry import propagate
    except ImportError:
        return None
    carrier = {}
    propagate.inject(carrier)
    return carrier or None


@contextmanager
def use_context(carrier):
    """Attach the span context decoded from ``carrier`` for the duration
    of the ``with`` block.

    No-op when observability is disabled, ``carrier`` is falsy, or
    OpenTelemetry is unavailable. The wrapped body always runs;
    ``detach`` is guaranteed even when the body raises.
    """
    if not _observability_enabled() or not carrier:
        yield
        return
    try:
        from opentelemetry import context as otel_context
        from opentelemetry import propagate
    except ImportError:
        yield
        return
    extracted = propagate.extract(carrier)
    token = otel_context.attach(extracted)
    try:
        yield
    finally:
        otel_context.detach(token)
