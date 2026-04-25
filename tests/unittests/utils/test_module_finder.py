"""Unit tests for ``pdip.utils.module_finder.ModuleFinder``.

The existing ``test_utils.py`` only exercises the ``Modules not
found`` path of ``get_module``. This module targets the branches
that are not hit elsewhere:

- ``find_last_parent_module`` both when ``sys.path`` contains the
  root directory (returns ``None``) and when it points to a parent
  (returns the relative module name).
- ``find_all_modules`` with ``running_directory != root_directory``
  (sets ``module_base_address`` from the relative path) and with
  ``running_directory == root_directory`` followed by a
  ``find_last_parent_module`` hit (sets ``module_last_parent_address``).
- ``get_module`` happy path with exactly one matching module.
- ``import_modules_by_name_ends_with`` when the module is already in
  ``sys.modules`` (skips import) and when it is not (imports).
- ``import_modules`` with an ``included_modules`` filter, a
  ``ModuleNotFoundError`` + ``module_base_address`` fallback, a
  ``module_last_parent_address`` prefix join, and a ``KeyError``
  swallow on the retry path.
- ``cleanup`` removing previously-imported entries from
  ``sys.modules``.

Tests use ``tempfile.TemporaryDirectory`` plus an isolated
``sys.path`` / ``sys.modules`` snapshot so no state leaks across
tests.
"""

import os
import sys
import tempfile
from unittest import TestCase
from unittest.mock import patch

from pdip.utils.module_finder import ModuleFinder


def _write_package(root, name):
    """Create a package directory with an empty ``__init__.py`` and a
    single ``mymodule.py`` that defines ``VALUE = 1``."""
    pkg = os.path.join(root, name)
    os.makedirs(pkg, exist_ok=True)
    with open(os.path.join(pkg, "__init__.py"), "w") as fh:
        fh.write("")
    with open(os.path.join(pkg, "mymodule.py"), "w") as fh:
        fh.write("VALUE = 1\n")
    return pkg


class _SysPathSandbox:
    """Snapshot sys.path / sys.modules, restore on exit."""

    def __enter__(self):
        self._path = list(sys.path)
        self._modules = set(sys.modules.keys())
        return self

    def __exit__(self, exc_type, exc, tb):
        sys.path[:] = self._path
        # Remove anything new added during the test.
        for name in list(sys.modules.keys()):
            if name not in self._modules:
                del sys.modules[name]


class ModuleFinderFindLastParentModule(TestCase):
    def test_returns_none_when_sys_path_contains_root_itself(self):
        with tempfile.TemporaryDirectory() as tmp, _SysPathSandbox():
            sys.path.insert(0, tmp)
            finder = ModuleFinder(root_directory=tmp, initialize=False)

            self.assertIsNone(finder.find_last_parent_module())

    def test_returns_relative_module_name_when_sys_path_is_parent(self):
        with tempfile.TemporaryDirectory() as tmp, _SysPathSandbox():
            sub = os.path.join(tmp, "child")
            os.makedirs(sub, exist_ok=True)
            # sys.path points at the parent, root is the child dir:
            # the method should return ``"child"``.
            sys.path.insert(0, tmp)
            finder = ModuleFinder(root_directory=sub, initialize=False)

            self.assertEqual(finder.find_last_parent_module(), "child")


class ModuleFinderFindAllModulesBranches(TestCase):
    def test_sets_module_base_address_when_cwd_differs_from_root(self):
        with tempfile.TemporaryDirectory() as tmp, _SysPathSandbox():
            # Running dir == tmp; root == tmp/inner. Base address
            # becomes ``"inner"``. A single submodule ``pkg/mymodule``
            # lives under root so find_all_modules records it.
            inner = os.path.join(tmp, "inner")
            os.makedirs(inner, exist_ok=True)
            _write_package(inner, "pkg")

            with patch("os.getcwd", return_value=tmp):
                finder = ModuleFinder(root_directory=inner)

            self.assertTrue(finder.modules)
            base_addresses = {m["module_base_address"] for m in finder.modules}
            self.assertEqual(base_addresses, {"inner"})

    def test_sets_module_last_parent_address_when_cwd_equals_root(self):
        with tempfile.TemporaryDirectory() as tmp, _SysPathSandbox():
            sub = os.path.join(tmp, "child")
            os.makedirs(sub, exist_ok=True)
            _write_package(sub, "pkg")
            # Running dir == root == ``sub``; sys.path contains the
            # parent, so ``find_last_parent_module`` returns "child".
            sys.path.insert(0, tmp)

            with patch("os.getcwd", return_value=sub):
                finder = ModuleFinder(root_directory=sub)

            self.assertTrue(finder.modules)
            last_parents = {m["module_last_parent_address"] for m in finder.modules}
            self.assertEqual(last_parents, {"child"})


class ModuleFinderGetModuleHappyPath(TestCase):
    def test_get_module_returns_imported_single_match(self):
        with tempfile.TemporaryDirectory() as tmp, _SysPathSandbox():
            pkg_name = "modfind_getmod_pkg"
            _write_package(tmp, pkg_name)
            sys.path.insert(0, tmp)

            with patch("os.getcwd", return_value=tmp):
                finder = ModuleFinder(root_directory=tmp)

            module = finder.get_module("mymodule")

            # The single-match branch imports the address and returns it.
            self.assertIsNotNone(module)
            self.assertEqual(module.VALUE, 1)


class ModuleFinderImportByNameEndsWith(TestCase):
    def test_imports_module_matching_suffix_when_not_already_in_sys_modules(self):
        with tempfile.TemporaryDirectory() as tmp, _SysPathSandbox():
            pkg_name = "modfind_suffix_pkg"
            _write_package(tmp, pkg_name)
            sys.path.insert(0, tmp)

            with patch("os.getcwd", return_value=tmp):
                finder = ModuleFinder(root_directory=tmp)

            # Sanity: the target module is not yet imported.
            module_address = f"{pkg_name}.mymodule"
            self.assertNotIn(module_address, sys.modules)

            finder.import_modules_by_name_ends_with("mymodule")

            self.assertIn(module_address, sys.modules)

    def test_skips_module_matching_suffix_when_already_in_sys_modules(self):
        with tempfile.TemporaryDirectory() as tmp, _SysPathSandbox():
            pkg_name = "modfind_suffix_skip_pkg"
            _write_package(tmp, pkg_name)
            sys.path.insert(0, tmp)

            with patch("os.getcwd", return_value=tmp):
                finder = ModuleFinder(root_directory=tmp)

            module_address = f"{pkg_name}.mymodule"
            # Pre-register a sentinel module so the branch that skips
            # ``importlib.import_module`` is exercised.
            sys.modules[module_address] = "sentinel"

            with patch(
                "pdip.utils.module_finder.importlib.import_module"
            ) as imp:
                finder.import_modules_by_name_ends_with("mymodule")

                imp.assert_not_called()
            # Module is left in place untouched.
            self.assertEqual(sys.modules[module_address], "sentinel")


class ModuleFinderImportModulesFiltersAndFallback(TestCase):
    def test_included_filter_skips_non_matching_modules(self):
        with tempfile.TemporaryDirectory() as tmp, _SysPathSandbox():
            pkg_a = "modfind_filter_a"
            pkg_b = "modfind_filter_b"
            _write_package(tmp, pkg_a)
            _write_package(tmp, pkg_b)
            sys.path.insert(0, tmp)

            with patch("os.getcwd", return_value=tmp):
                finder = ModuleFinder(root_directory=tmp)

            # Only include pkg_a — pkg_b must stay unimported.
            finder.import_modules(included_modules=[pkg_a])

            self.assertIn(f"{pkg_a}.mymodule", sys.modules)
            self.assertNotIn(f"{pkg_b}.mymodule", sys.modules)

    def test_modulenotfounderror_retries_with_module_base_address(self):
        # The first import attempt raises ModuleNotFoundError; the retry
        # uses ``module_base_address`` (when present) to build a new
        # name. We patch importlib.import_module so we can observe both
        # calls without a real module layout.
        with tempfile.TemporaryDirectory() as tmp, _SysPathSandbox():
            with patch("os.getcwd", return_value=tmp):
                finder = ModuleFinder(root_directory=tmp, initialize=False)
            finder.modules = [
                {
                    "module_name": "mymodule",
                    "file_path": "/ignored",
                    "module_path": os.path.join(tmp, "pkg", "mymodule"),
                    "module_address": "pkg.mymodule",
                    "module_base_address": "base",
                    "module_parent_address": "pkg",
                    "module_last_parent_address": "",
                }
            ]
            with patch(
                "pdip.utils.module_finder.importlib.import_module"
            ) as imp:
                imp.side_effect = [ModuleNotFoundError("first"), None]

                finder.import_modules()

                self.assertEqual(imp.call_count, 2)
                # Second call uses the base-prefixed full address.
                self.assertEqual(
                    imp.call_args_list[1].args[0], "base.pkg.mymodule"
                )

    def test_modulenotfounderror_retry_swallows_keyerror(self):
        with tempfile.TemporaryDirectory() as tmp, _SysPathSandbox():
            with patch("os.getcwd", return_value=tmp):
                finder = ModuleFinder(root_directory=tmp, initialize=False)
            finder.modules = [
                {
                    "module_name": "mymodule",
                    "file_path": "/ignored",
                    "module_path": os.path.join(tmp, "pkg", "mymodule"),
                    "module_address": "pkg.mymodule",
                    "module_base_address": "",
                    "module_parent_address": "pkg",
                    "module_last_parent_address": "",
                }
            ]
            with patch(
                "pdip.utils.module_finder.importlib.import_module"
            ) as imp:
                imp.side_effect = [ModuleNotFoundError("first"), KeyError("x")]

                # The bug the module guards against: the retry path
                # swallows KeyError silently. No exception must escape.
                finder.import_modules()

                self.assertEqual(imp.call_count, 2)

    def test_uses_module_last_parent_address_prefix_when_set(self):
        with tempfile.TemporaryDirectory() as tmp, _SysPathSandbox():
            with patch("os.getcwd", return_value=tmp):
                finder = ModuleFinder(root_directory=tmp, initialize=False)
            finder.modules = [
                {
                    "module_name": "mymodule",
                    "file_path": "/ignored",
                    "module_path": os.path.join(tmp, "pkg", "mymodule"),
                    "module_address": "pkg.mymodule",
                    "module_base_address": "",
                    "module_parent_address": "pkg",
                    "module_last_parent_address": "top",
                }
            ]
            with patch(
                "pdip.utils.module_finder.importlib.import_module"
            ) as imp:
                imp.return_value = None

                finder.import_modules()

                imp.assert_called_once_with("top.pkg.mymodule")

    def test_uncaught_non_modulenotfound_exception_triggers_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp, _SysPathSandbox():
            with patch("os.getcwd", return_value=tmp):
                finder = ModuleFinder(root_directory=tmp, initialize=False)
            finder.modules = [
                {
                    "module_name": "mymodule",
                    "file_path": "/ignored",
                    "module_path": os.path.join(tmp, "pkg", "mymodule"),
                    "module_address": "pkg.mymodule",
                    "module_base_address": "",
                    "module_parent_address": "pkg",
                    "module_last_parent_address": "",
                }
            ]
            with patch(
                "pdip.utils.module_finder.importlib.import_module"
            ) as imp, patch.object(finder, "cleanup") as cleanup:
                imp.side_effect = RuntimeError("boom")

                with self.assertRaises(RuntimeError):
                    finder.import_modules()

                cleanup.assert_called_once()


class ModuleFinderCleanup(TestCase):
    def test_cleanup_removes_any_sys_modules_entry_matching_address(self):
        with tempfile.TemporaryDirectory() as tmp, _SysPathSandbox():
            with patch("os.getcwd", return_value=tmp):
                finder = ModuleFinder(root_directory=tmp, initialize=False)
            finder.modules = [
                {
                    "module_name": "mymodule",
                    "file_path": "/ignored",
                    "module_path": os.path.join(tmp, "pkg", "mymodule"),
                    "module_address": "unique_cleanup_pkg.mymodule",
                    "module_base_address": "",
                    "module_parent_address": "unique_cleanup_pkg",
                    "module_last_parent_address": "",
                }
            ]
            sys.modules["unique_cleanup_pkg.mymodule"] = "sentinel"
            sys.modules["unique_cleanup_pkg"] = "parent-sentinel"

            finder.cleanup()

            self.assertNotIn("unique_cleanup_pkg.mymodule", sys.modules)
            self.assertNotIn("unique_cleanup_pkg", sys.modules)
