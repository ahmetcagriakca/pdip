"""Stub the ``pandas`` module in ``sys.modules`` before any
``pdip.integrator.*`` import that transitively pulls it in.

``pandas`` was removed from ``requirements.txt`` in the 3.14 readiness
work — it lives only in the ``integrator`` extra because only the
adapter code imports it at runtime. Unit tests that exercise the
orchestration layer (Integrator, IntegrationExecution, OperationExecution)
touch modules whose package ``__init__`` chain eventually imports a
file that does ``from pandas import DataFrame``. The tests themselves
never call pandas, so a stub is sufficient.

Import this module first from any integrator-orchestration test file:

    # noqa: F401
    from tests.unittests.integrator import _stub_pandas  # noqa: E402

The side effect happens at import time.
"""

import sys
import types
from unittest.mock import MagicMock


if "pandas" not in sys.modules:
    stub = types.ModuleType("pandas")
    stub.DataFrame = MagicMock(name="DataFrame")
    stub.notnull = MagicMock(name="notnull")
    stub.isnull = MagicMock(name="isnull")
    sys.modules["pandas"] = stub


# ``func_timeout`` lives behind the same ``integrator`` extra as pandas;
# the parallel-thread strategy imports ``FunctionTimedOut`` / ``func_set_timeout``
# at module load. A stub is enough for unit tests that never exercise
# the decorated paths.
if "func_timeout" not in sys.modules:
    ft = types.ModuleType("func_timeout")
    ft.FunctionTimedOut = type("FunctionTimedOut", (Exception,), {})
    ft.func_set_timeout = lambda *args, **kwargs: (lambda fn: fn)
    sys.modules["func_timeout"] = ft
