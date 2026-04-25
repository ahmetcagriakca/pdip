"""Machine-enforced slice of ADR-0026 (test quality rules).

Each test in this module walks the rest of the test tree and fails
CI when a quality rule is violated. The rules encoded here are the
ones that are cheap to check statically; rules that require
behavioural judgement (naming, AAA structure, negative-case
coverage) live in review per ADR-0026 §G.2.

If a rule is too strict for a one-off case, add the file (relative
to the repository root) to the corresponding allow-list constant
below **with a comment explaining why** — ADR-0026 §G.3.
"""

import ast
import importlib
import inspect
import json
import pathlib
import re
from unittest import TestCase


# ---------------------------------------------------------------------------
# Setup — locate the test tree and collect every .py file once.
# ---------------------------------------------------------------------------


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_TESTS_ROOT = _REPO_ROOT / "tests"
_UNIT_ROOT = _TESTS_ROOT / "unittests"


def _iter_test_files(root: pathlib.Path):
    for path in sorted(root.rglob("*.py")):
        if "quality_guard" in path.parts:
            # Skip the guard itself — it's allowed to mention the
            # forbidden patterns inside regexes and docstrings.
            continue
        if "__pycache__" in path.parts:
            continue
        yield path


def _iter_unit_test_methods():
    """Yield ``(path, class_node, func_node)`` tuples for every
    ``test_*`` method inside a ``unittest.TestCase`` subclass under
    ``tests/unittests/``."""
    for path in _iter_test_files(_UNIT_ROOT):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            # A syntax error elsewhere will be caught by the suite
            # itself; don't duplicate the failure here.
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not any(
                _is_testcase_base(b) for b in node.bases
            ):
                continue
            for item in node.body:
                if isinstance(
                    item, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and item.name.startswith("test_"):
                    yield path, node, item


def _is_testcase_base(base_node):
    """Best-effort check for ``TestCase`` / ``unittest.TestCase``
    bases. Misses exotic aliasing; that's fine — this is a soft
    filter, not an auth boundary."""
    if isinstance(base_node, ast.Name):
        return base_node.id == "TestCase"
    if isinstance(base_node, ast.Attribute):
        return base_node.attr == "TestCase"
    return False


def _contains_assertion(func_node):
    """True if the function node contains at least one ``assert``
    statement (bare) or any call to a method whose name starts with
    ``assert`` (``self.assertEqual``, ``self.assertRaises`` …)."""
    for sub in ast.walk(func_node):
        if isinstance(sub, ast.Assert):
            return True
        if isinstance(sub, ast.Call):
            func = sub.func
            if isinstance(func, ast.Attribute) and func.attr.startswith("assert"):
                return True
    return False


# ---------------------------------------------------------------------------
# Rule A.1 — every test method has at least one assertion.
# ---------------------------------------------------------------------------


# Files (relative to repo root) allowed to contain tests without
# assertions. Each entry needs a comment with the reason.
_A1_ALLOWLIST: frozenset[str] = frozenset()


class RuleA1EveryTestMethodAsserts(TestCase):
    def test_every_test_method_contains_an_assertion(self):
        offenders = []
        for path, cls, func in _iter_unit_test_methods():
            rel = str(path.relative_to(_REPO_ROOT))
            if rel in _A1_ALLOWLIST:
                continue
            if _contains_assertion(func):
                continue
            offenders.append(f"{rel}::{cls.name}::{func.name} (line {func.lineno})")
        self.assertEqual(
            offenders,
            [],
            "ADR-0026 A.1: every test method must contain at least one "
            "assertion. Offenders:\n  " + "\n  ".join(offenders),
        )


# ---------------------------------------------------------------------------
# Rule A.2 — no tautological assertions.
# ---------------------------------------------------------------------------


_A2_TAUTOLOGY_PATTERNS = [
    re.compile(r"\bassertTrue\s*\(\s*True\s*[,)]"),
    re.compile(r"\bassertFalse\s*\(\s*False\s*[,)]"),
    re.compile(r"^\s*assert\s+True\s*(?:,|$)"),
    re.compile(r"^\s*assert\s+False\s*,"),  # ``assert False, "msg"`` is a deliberate fail
    re.compile(r"\bassertEqual\s*\(\s*(\w+)\s*,\s*\1\s*\)"),
]


class RuleA2NoTautologicalAssertions(TestCase):
    def test_no_tautological_assertions_in_the_test_tree(self):
        offenders = []
        for path in _iter_test_files(_TESTS_ROOT):
            # The guard itself must be allowed to mention these
            # patterns in its regexes.
            if path == pathlib.Path(__file__):
                continue
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                for pattern in _A2_TAUTOLOGY_PATTERNS:
                    if pattern.search(line):
                        rel = str(path.relative_to(_REPO_ROOT))
                        offenders.append(f"{rel}:{lineno}: {line.strip()}")
        self.assertEqual(
            offenders,
            [],
            "ADR-0026 A.2: tautological assertions forbidden. Offenders:\n  "
            + "\n  ".join(offenders),
        )


# ---------------------------------------------------------------------------
# Rule D.1 — no long sleeps in unit tests.
# ---------------------------------------------------------------------------


_SLEEP_PATTERN = re.compile(r"\btime\.sleep\s*\(\s*([0-9]*\.?[0-9]+)\s*\)")
_D1_THRESHOLD_SECONDS = 0.1


class RuleD1NoLongSleeps(TestCase):
    def test_no_unit_test_sleeps_over_threshold(self):
        offenders = []
        for path in _iter_test_files(_UNIT_ROOT):
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                match = _SLEEP_PATTERN.search(line)
                if not match:
                    continue
                value = float(match.group(1))
                if value >= _D1_THRESHOLD_SECONDS:
                    rel = str(path.relative_to(_REPO_ROOT))
                    offenders.append(
                        f"{rel}:{lineno}: time.sleep({value}) — limit {_D1_THRESHOLD_SECONDS}s"
                    )
        self.assertEqual(
            offenders,
            [],
            "ADR-0026 D.1: no time.sleep >= "
            f"{_D1_THRESHOLD_SECONDS}s in unit tests. Offenders:\n  "
            + "\n  ".join(offenders),
        )


# ---------------------------------------------------------------------------
# Rule F.1 — unittest only, no pytest-isms in the test tree.
# ---------------------------------------------------------------------------


_PYTEST_IMPORT_PATTERN = re.compile(
    r"^\s*(?:from\s+pytest\b|import\s+pytest\b)"
)


class RuleF1UnittestOnly(TestCase):
    def test_no_pytest_imports_under_tests(self):
        offenders = []
        for path in _iter_test_files(_TESTS_ROOT):
            if path == pathlib.Path(__file__):
                continue
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if _PYTEST_IMPORT_PATTERN.match(line):
                    rel = str(path.relative_to(_REPO_ROOT))
                    offenders.append(f"{rel}:{lineno}: {line.strip()}")
        self.assertEqual(
            offenders,
            [],
            "ADR-0026 F.1: pdip uses unittest. Offenders:\n  "
            + "\n  ".join(offenders),
        )


# ---------------------------------------------------------------------------
# Rule F.2 — no star imports anywhere under tests/.
# ---------------------------------------------------------------------------


_STAR_IMPORT_PATTERN = re.compile(r"^\s*from\s+\S+\s+import\s+\*\s*$")


class RuleF2NoStarImports(TestCase):
    def test_no_star_imports_in_test_tree(self):
        offenders = []
        for path in _iter_test_files(_TESTS_ROOT):
            if path == pathlib.Path(__file__):
                continue
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if _STAR_IMPORT_PATTERN.match(line):
                    rel = str(path.relative_to(_REPO_ROOT))
                    offenders.append(f"{rel}:{lineno}: {line.strip()}")
        self.assertEqual(
            offenders,
            [],
            "ADR-0026 F.2: no star imports in tests/. Offenders:\n  "
            + "\n  ".join(offenders),
        )


# ---------------------------------------------------------------------------
# Rule ADR-0027 §5 — ``# pragma: no cover`` must carry a one-line
# reason comment on the same line (or the line immediately above it
# when the pragma is on its own line).
# ---------------------------------------------------------------------------


_PRAGMA_NO_COVER_PATTERN = re.compile(r"#\s*pragma:\s*no\s+cover")


def _has_pragma_reason(line: str) -> bool:
    """True when a line with ``# pragma: no cover`` also carries an
    explanatory comment immediately after the pragma on the same line,
    e.g. ``foo = 1  # pragma: no cover — constructed only in prod``.

    We look for any non-whitespace text after the ``no cover`` token
    (other than a trailing closing parenthesis, a colon, a comma, or
    line-continuation characters). A pragma that lives on its own line
    with no explanation is rejected."""
    match = _PRAGMA_NO_COVER_PATTERN.search(line)
    if not match:
        return True
    tail = line[match.end():].strip()
    # Strip punctuation characters that sometimes trail a pragma
    # without adding meaning.
    for ch in "():,;\\":
        tail = tail.replace(ch, " ")
    return bool(tail.strip())


class RuleADR0027PragmaNoCoverHasReason(TestCase):
    def test_every_pragma_no_cover_has_an_inline_reason(self):
        offenders = []
        src_root = _REPO_ROOT / "pdip"
        for path in sorted(src_root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if not _PRAGMA_NO_COVER_PATTERN.search(line):
                    continue
                if _has_pragma_reason(line):
                    continue
                rel = str(path.relative_to(_REPO_ROOT))
                offenders.append(f"{rel}:{lineno}: {line.strip()}")
        self.assertEqual(
            offenders,
            [],
            "ADR-0027 §5: every ``# pragma: no cover`` must carry an "
            "inline reason comment on the same line. Offenders:\n  "
            + "\n  ".join(offenders),
        )


# ---------------------------------------------------------------------------
# Rule ADR-0034 §1 — every directory directly under ``pdip/`` with an
# ``__init__.py`` must either appear in ``EXPECTED_PUBLIC_SURFACE``
# (the documented public surface — see
# ``tests/unittests/public_api/test_public_api_contract.py``) or be in
# the explicit internal allowlist below with a one-line reason
# comment. This catches a brand-new top-level package that was added
# without a public-API decision being made.
# ---------------------------------------------------------------------------


# Top-level subpackages that exist under ``pdip/`` but are
# intentionally NOT part of the 1.0 public surface. Each entry needs
# a comment explaining why — same convention as the other allow-list
# constants in this file (ADR-0026 §G.3).
_ADR0034_INTERNAL_PACKAGES: frozenset[str] = frozenset({
    # ``pdip.base`` re-exports ``Pdi``, the framework's bootstrap
    # entry point. Kept internal pre-1.0 because the bootstrap
    # surface is being audited under ADR-0034 and the public
    # signature is not yet frozen.
    "base",
})


class RuleADR0034NoUndocumentedTopLevelPackage(TestCase):
    def test_every_pdip_subpackage_is_either_public_or_internal_allowlisted(self):
        # Resolve the documented public surface from its single
        # source of truth — re-importing the contract test module is
        # cheap and keeps the two artefacts in lockstep without
        # duplicating the surface list here.
        from tests.unittests.public_api.test_public_api_contract import (
            EXPECTED_PUBLIC_SURFACE,
        )
        documented = set()
        for fqn in EXPECTED_PUBLIC_SURFACE:
            if fqn == "pdip":
                continue
            if not fqn.startswith("pdip."):
                continue
            tail = fqn[len("pdip."):]
            if "." in tail:
                # Sub-subpackage — out of scope for this rule.
                continue
            documented.add(tail)

        offenders = []
        src_root = _REPO_ROOT / "pdip"
        for child in sorted(src_root.iterdir()):
            if not child.is_dir():
                continue
            if child.name == "__pycache__":
                continue
            if not (child / "__init__.py").exists():
                continue
            if child.name in documented:
                continue
            if child.name in _ADR0034_INTERNAL_PACKAGES:
                continue
            offenders.append(f"pdip.{child.name}")

        self.assertEqual(
            offenders,
            [],
            "ADR-0034 §1: every top-level ``pdip/`` subpackage must "
            "appear in EXPECTED_PUBLIC_SURFACE (and in "
            "docs/public-api.md) OR in this rule's "
            "_ADR0034_INTERNAL_PACKAGES allowlist with a one-line "
            "reason comment. New packages are not silently public. "
            "Offenders:\n  " + "\n  ".join(offenders),
        )


# ---------------------------------------------------------------------------
# Rule ADR-0035 §3 — every public symbol's rendered signature must match
# the checked-in snapshot at ``docs/public-api-signatures.json``. The
# snapshot is the third (signature) enforcement layer described by
# ADR-0034 §5; ADR-0035 picks the baseline source (checked-in JSON) and
# the rendered format (``"class X" + str(inspect.signature(X.__init__))``
# / ``"def f" + str(inspect.signature(f))`` / ``repr(value)``).
#
# A change of any kind — addition, removal, or signature edit — fails
# CI. To land an intentional public-signature change, run
# ``python scripts/regenerate_public_api_signatures.py
# > docs/public-api-signatures.json`` in the same PR, and follow the
# ADR-0034 §3 deprecation policy for removals.
# ---------------------------------------------------------------------------


_PUBLIC_API_SIGNATURE_SNAPSHOT_PATH = (
    _REPO_ROOT / "docs" / "public-api-signatures.json"
)


def _render_public_signature(symbol_name: str, value: object) -> str:
    """Canonical signature text per ADR-0035 §2. Identical formatting
    to ``scripts/regenerate_public_api_signatures.py`` so the guard
    and the regen helper round-trip 1:1."""
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


class RuleADR0035PublicApiSignatureSnapshotMatches(TestCase):
    def test_public_signatures_match_the_checked_in_snapshot(self):
        from tests.unittests.public_api.test_public_api_contract import (
            EXPECTED_PUBLIC_SURFACE,
        )
        snapshot = json.loads(
            _PUBLIC_API_SIGNATURE_SNAPSHOT_PATH.read_text(encoding="utf-8")
        )

        actual = {}
        for package_name, names in EXPECTED_PUBLIC_SURFACE.items():
            if not names:
                continue
            module = importlib.import_module(package_name)
            for symbol_name in names:
                value = getattr(module, symbol_name)
                key = f"{package_name}.{symbol_name}"
                actual[key] = _render_public_signature(symbol_name, value)

        diffs = []
        for key in sorted(set(snapshot) | set(actual)):
            if key in snapshot and key in actual:
                if snapshot[key] != actual[key]:
                    diffs.append(
                        f"{key}: CHANGED\n      "
                        f"snapshot: {snapshot[key]}\n      "
                        f"actual:   {actual[key]}"
                    )
            elif key in snapshot:
                diffs.append(
                    f"{key}: REMOVED — was {snapshot[key]!r}"
                )
            else:
                diffs.append(
                    f"{key}: ADDED — now {actual[key]!r}"
                )

        self.assertEqual(
            diffs,
            [],
            "ADR-0035 §3: public-API signature drift detected. "
            "If this change is intentional, regenerate the snapshot "
            "with `python scripts/regenerate_public_api_signatures.py "
            "> docs/public-api-signatures.json` and follow the "
            "ADR-0034 §3 deprecation policy for any removals. "
            "Drift:\n  " + "\n  ".join(diffs),
        )


# ---------------------------------------------------------------------------
# Rules ADR-0036 §2 — automating the warning-bearing-prior-release
# check ADR-0034 §3 currently enforces in review.
#
# Two rules:
#  - RuleADR0036DeprecationWarningHasManifestEntry walks ``pdip/`` for
#    ``warnings.warn(..., DeprecationWarning)`` calls and asserts the
#    enclosing symbol appears as a key in
#    ``docs/public-api-deprecations.json``.
#  - RuleADR0036RemovalRespectsDeprecationCycle cross-checks the
#    ADR-0035 signature-snapshot REMOVED diff against the manifest:
#    every removed key must be in the manifest with ``removable_in``
#    less than or equal to ``pdip.__version__``.
#
# To deprecate a public symbol:
#   1. Emit ``warnings.warn("X is deprecated since Y, use Z;
#      removable in W", DeprecationWarning)`` from the symbol body.
#   2. Add the symbol's qualified key to the manifest with
#      ``deprecated_in`` / ``removable_in`` / ``replacement`` /
#      ``reason``.
#   3. Ship the minor.
#   4. In the major where ``removable_in`` lands, remove the symbol
#      AND its manifest entry together — both rules go quiet at the
#      same time.
# ---------------------------------------------------------------------------


_PUBLIC_API_DEPRECATIONS_MANIFEST_PATH = (
    _REPO_ROOT / "docs" / "public-api-deprecations.json"
)


def _is_deprecation_warning_arg(node):
    """True when ``node`` denotes ``DeprecationWarning`` — either as
    a bare ``Name`` (``warnings.warn(msg, DeprecationWarning)``) or
    as an attribute (``warnings.warn(msg, builtins.DeprecationWarning)``).
    """
    if isinstance(node, ast.Name) and node.id == "DeprecationWarning":
        return True
    if isinstance(node, ast.Attribute) and node.attr == "DeprecationWarning":
        return True
    return False


def _call_is_warnings_warn(call_node):
    """True when ``call_node`` is a ``warnings.warn(...)`` invocation
    — handles ``warnings.warn`` (attribute access on the imported
    module) and the bare ``warn`` form when the function was
    re-exported with ``from warnings import warn``."""
    func = call_node.func
    if isinstance(func, ast.Attribute) and func.attr == "warn":
        if isinstance(func.value, ast.Name) and func.value.id == "warnings":
            return True
    if isinstance(func, ast.Name) and func.id == "warn":
        # Likely ``from warnings import warn`` — treat as a candidate.
        # The DeprecationWarning category check still gates whether
        # this counts as a deprecation site.
        return True
    return False


def _call_emits_deprecation_warning(call_node):
    """True when ``call_node`` is a ``warnings.warn(...)`` call whose
    category (positional second arg or ``category=`` kwarg) names
    ``DeprecationWarning``."""
    if not _call_is_warnings_warn(call_node):
        return False
    if len(call_node.args) >= 2 and _is_deprecation_warning_arg(
            call_node.args[1]
    ):
        return True
    for kw in call_node.keywords:
        if kw.arg == "category" and _is_deprecation_warning_arg(kw.value):
            return True
    return False


def _module_qualname_for_pdip_path(path):
    """Translate ``pdip/foo/bar.py`` into ``pdip.foo.bar``."""
    rel = path.relative_to(_REPO_ROOT)
    parts = list(rel.parts)
    parts[-1] = parts[-1][:-len(".py")] if parts[-1].endswith(".py") else parts[-1]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _enclosing_qualname(stack, module_qualname):
    """Compose ``<module>.<Class>.<func>`` from the ``ast``-walk
    enclosing-scope ``stack`` (built from ``ClassDef`` / ``FunctionDef``
    / ``AsyncFunctionDef`` names in source order)."""
    if not stack:
        return module_qualname
    return f"{module_qualname}." + ".".join(stack)


def _walk_with_scope(tree, module_qualname):
    """Yield ``(qualname, call_node)`` for every ``Call`` in ``tree``
    paired with the qualified name of its enclosing scope."""
    stack = []

    def visit(node):
        if isinstance(node, ast.ClassDef):
            stack.append(node.name)
            for child in ast.iter_child_nodes(node):
                yield from visit(child)
            stack.pop()
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stack.append(node.name)
            for child in ast.iter_child_nodes(node):
                yield from visit(child)
            stack.pop()
            return
        if isinstance(node, ast.Call):
            yield _enclosing_qualname(stack, module_qualname), node
        for child in ast.iter_child_nodes(node):
            yield from visit(child)

    yield from visit(tree)


def _load_deprecations_manifest():
    return json.loads(
        _PUBLIC_API_DEPRECATIONS_MANIFEST_PATH.read_text(encoding="utf-8")
    )


def _parse_semver(version_string):
    """Return a ``(major, minor, patch)`` tuple suitable for
    comparison. Tolerates ``"1.0.0"`` and ``"1.0"`` shapes; anything
    weirder falls back to ``(0, 0, 0)`` so the comparison still
    behaves predictably."""
    parts = version_string.split(".")
    out = []
    for part in parts[:3]:
        # Strip any pre-release / build suffix attached to the patch
        # (e.g. ``"1.0.0rc1"`` → 1.0.0 for ordering purposes).
        digits = ""
        for ch in part:
            if ch.isdigit():
                digits += ch
            else:
                break
        out.append(int(digits) if digits else 0)
    while len(out) < 3:
        out.append(0)
    return tuple(out)


class RuleADR0036DeprecationWarningHasManifestEntry(TestCase):
    def test_every_deprecation_warning_call_has_a_manifest_entry(self):
        manifest = _load_deprecations_manifest()
        offenders = []
        src_root = _REPO_ROOT / "pdip"
        for path in sorted(src_root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            try:
                tree = ast.parse(
                    path.read_text(encoding="utf-8"), filename=str(path)
                )
            except SyntaxError:
                continue
            module_qualname = _module_qualname_for_pdip_path(path)
            for qualname, call_node in _walk_with_scope(
                    tree, module_qualname
            ):
                if not _call_emits_deprecation_warning(call_node):
                    continue
                if qualname in manifest:
                    continue
                rel = str(path.relative_to(_REPO_ROOT))
                offenders.append(
                    f"{rel}:{call_node.lineno}: ``warnings.warn(..., "
                    f"DeprecationWarning)`` from ``{qualname}`` is "
                    "missing from docs/public-api-deprecations.json"
                )
        self.assertEqual(
            offenders,
            [],
            "ADR-0036 §2: every public-symbol deprecation warning "
            "must register an entry in "
            "docs/public-api-deprecations.json with "
            "``deprecated_in`` / ``removable_in`` / ``replacement`` "
            "/ ``reason`` per ADR-0036 §1. Offenders:\n  "
            + "\n  ".join(offenders),
        )


class RuleADR0036RemovalRespectsDeprecationCycle(TestCase):
    def test_every_removed_public_symbol_was_deprecated_and_due(self):
        from tests.unittests.public_api.test_public_api_contract import (
            EXPECTED_PUBLIC_SURFACE,
        )
        import pdip

        snapshot = json.loads(
            _PUBLIC_API_SIGNATURE_SNAPSHOT_PATH.read_text(encoding="utf-8")
        )
        live_keys = set()
        for package_name, names in EXPECTED_PUBLIC_SURFACE.items():
            for symbol_name in names:
                live_keys.add(f"{package_name}.{symbol_name}")
        removed_keys = sorted(set(snapshot) - live_keys)

        if not removed_keys:
            # Nothing removed — nothing to police.
            self.assertEqual(removed_keys, [])
            return

        manifest = _load_deprecations_manifest()
        current_version = _parse_semver(pdip.__version__)

        offenders = []
        for key in removed_keys:
            entry = manifest.get(key)
            if entry is None:
                offenders.append(
                    f"{key}: REMOVED without a "
                    "docs/public-api-deprecations.json entry. "
                    "ADR-0034 §3 requires a prior-minor "
                    "DeprecationWarning."
                )
                continue
            removable_in = entry.get("removable_in")
            if removable_in is None:
                offenders.append(
                    f"{key}: manifest entry has no ``removable_in`` "
                    "field — cannot decide whether the removal is due."
                )
                continue
            if _parse_semver(removable_in) > current_version:
                offenders.append(
                    f"{key}: removable_in={removable_in} > current "
                    f"version {pdip.__version__}; the deprecation "
                    "cycle has not elapsed yet."
                )
        self.assertEqual(
            offenders,
            [],
            "ADR-0036 §2: a removed public symbol must appear in "
            "docs/public-api-deprecations.json with "
            "``removable_in`` <= pdip.__version__ before the "
            "removal is allowed (ADR-0034 §3 deprecation policy). "
            "Offenders:\n  " + "\n  ".join(offenders),
        )
