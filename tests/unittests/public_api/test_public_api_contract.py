"""Public-API contract test for ADR-0034 §1.

ADR-0034 says a symbol is part of the 1.0 public surface if and only
if it is reachable through one of the documented top-level
``__init__.py`` files. This test pins the *current* surface so any
future PR that removes, renames, or accidentally adds a public
symbol fails CI — forcing a deliberate decision (and, for removals,
the deprecation cycle defined in ADR-0034 §3).

When a public symbol is added or removed on purpose:

1. Update ``EXPECTED_PUBLIC_SURFACE`` below.
2. Update the matching ``__all__`` in ``pdip/<package>/__init__.py``.
3. Update the table in ``docs/public-api.md``.
4. If the change is a removal, follow the ADR-0034 §3 deprecation
   policy.

The three artefacts are kept in lockstep on purpose — the test is
the machine-checked contract.
"""

import importlib
from unittest import TestCase


# ---------------------------------------------------------------------------
# The frozen public surface — ADR-0034 §1.
# ---------------------------------------------------------------------------


EXPECTED_PUBLIC_SURFACE = {
    "pdip": (),
    "pdip.api": (),
    "pdip.configuration": (
        "ConfigManager",
    ),
    "pdip.cqrs": (
        "CommandQueryBase",
        "CommandQueryHandlerBase",
        "Dispatcher",
        "ICommand",
        "ICommandHandler",
        "IQuery",
        "IQueryHandler",
    ),
    "pdip.cryptography": (
        "CryptoService",
    ),
    "pdip.data": (),
    "pdip.delivery": (
        "EmailProvider",
    ),
    "pdip.dependency": (
        "IScoped",
        "ISingleton",
    ),
    "pdip.exceptions": (
        "IncompatibleAdapterException",
        "NotSupportedFeatureException",
        "OperationalException",
        "RequiredClassException",
    ),
    "pdip.html": (
        "HtmlTemplateService",
        "Pagination",
    ),
    "pdip.integrator": (),
    "pdip.io": (
        "FileManager",
        "FolderManager",
    ),
    "pdip.json": (
        "BaseConverter",
        "DateTimeEncoder",
        "JsonConvert",
        "MultipleJsonEncoders",
        "UUIDEncoder",
        "date_time_parser",
    ),
    "pdip.logging": (),
    "pdip.observability": (
        "get_meter",
        "get_tracer",
    ),
    "pdip.processing": (
        "ProcessManager",
    ),
    "pdip.utils": (
        "ModuleFinder",
        "TypeChecker",
        "Utils",
    ),
}


class PublicApiContractTests(TestCase):
    """Three rules, asserted independently for clear failure messages."""

    def test_every_documented_public_package_declares_dunder_all(self):
        """ADR-0034 §1 + §5: every public package must declare ``__all__``."""
        offenders = []
        for package_name in EXPECTED_PUBLIC_SURFACE:
            module = importlib.import_module(package_name)
            if not hasattr(module, "__all__"):
                offenders.append(package_name)
        self.assertEqual(
            offenders,
            [],
            "ADR-0034 §1: every public package must declare __all__. "
            "Offenders:\n  " + "\n  ".join(offenders),
        )

    def test_dunder_all_matches_documented_surface(self):
        """The frozen ``EXPECTED_PUBLIC_SURFACE`` is the contract;
        a drift here means ``docs/public-api.md`` is also out of date."""
        mismatches = []
        for package_name, expected in EXPECTED_PUBLIC_SURFACE.items():
            module = importlib.import_module(package_name)
            actual = tuple(sorted(module.__all__))
            documented = tuple(sorted(expected))
            if actual != documented:
                mismatches.append(
                    f"{package_name}: documented={documented!r} "
                    f"actual={actual!r}"
                )
        self.assertEqual(
            mismatches,
            [],
            "ADR-0034 §1: __all__ drift detected. Update "
            "EXPECTED_PUBLIC_SURFACE, the package's __all__, and "
            "docs/public-api.md together. Mismatches:\n  "
            + "\n  ".join(mismatches),
        )

    def test_every_name_in_dunder_all_resolves_on_the_module(self):
        """A name in ``__all__`` that does not actually exist on the
        module is a typo or a removed symbol; either way it is a
        broken contract."""
        offenders = []
        for package_name, expected in EXPECTED_PUBLIC_SURFACE.items():
            module = importlib.import_module(package_name)
            for symbol in expected:
                if not hasattr(module, symbol):
                    offenders.append(f"{package_name}::{symbol}")
        self.assertEqual(
            offenders,
            [],
            "ADR-0034 §1: every name in __all__ must be resolvable on "
            "the package. Offenders:\n  " + "\n  ".join(offenders),
        )

    def test_dunder_all_has_no_duplicates(self):
        """A duplicated symbol in ``__all__`` is silently tolerated by
        Python but is always a mistake."""
        offenders = []
        for package_name in EXPECTED_PUBLIC_SURFACE:
            module = importlib.import_module(package_name)
            names = list(module.__all__)
            if len(names) != len(set(names)):
                duplicates = sorted(
                    {name for name in names if names.count(name) > 1}
                )
                offenders.append(f"{package_name}: {duplicates}")
        self.assertEqual(
            offenders,
            [],
            "ADR-0034 §1: __all__ must not contain duplicates. "
            "Offenders:\n  " + "\n  ".join(offenders),
        )
