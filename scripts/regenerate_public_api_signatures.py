"""Regenerate ``docs/public-api-signatures.json`` (ADR-0035 §5).

Prints the canonical signature snapshot to stdout. Pipe into the
checked-in JSON file when an intentional public-signature change
lands:

.. code-block:: bash

   python scripts/regenerate_public_api_signatures.py \
       > docs/public-api-signatures.json

The format is the one defined in ADR-0035 §2 and read by
``RuleADR0035PublicApiSignatureSnapshotMatches`` in
``tests/unittests/quality_guard/test_conventions.py``. The
single source of truth for the public surface is
``EXPECTED_PUBLIC_SURFACE`` in
``tests/unittests/public_api/test_public_api_contract.py`` —
this script imports that mapping rather than re-listing the
packages here.
"""

import importlib
import inspect
import json
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ensure_project_on_sys_path() -> None:
    root = str(_project_root())
    if root not in sys.path:
        sys.path.insert(0, root)


def _render_signature(symbol_name: str, value: object) -> str:
    """Return the canonical text form for ``value`` per ADR-0035 §2."""
    if inspect.isclass(value):
        try:
            sig = inspect.signature(value.__init__)
        except (ValueError, TypeError):
            return f"class {symbol_name}"
        return f"class {symbol_name}{sig}"
    if callable(value):
        try:
            sig = inspect.signature(value)
        except (ValueError, TypeError):
            return f"def {symbol_name}"
        return f"def {symbol_name}{sig}"
    return repr(value)


def collect_public_signatures() -> dict:
    _ensure_project_on_sys_path()
    from tests.unittests.public_api.test_public_api_contract import (
        EXPECTED_PUBLIC_SURFACE,
    )

    snapshot: dict = {}
    for package_name, names in EXPECTED_PUBLIC_SURFACE.items():
        if not names:
            continue
        module = importlib.import_module(package_name)
        for symbol_name in names:
            value = getattr(module, symbol_name)
            key = f"{package_name}.{symbol_name}"
            snapshot[key] = _render_signature(symbol_name, value)
    return dict(sorted(snapshot.items()))


def main() -> None:
    snapshot = collect_public_signatures()
    print(json.dumps(snapshot, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
