"""Behavioural tests for ``pdip.io.folder_manager``.

All filesystem work happens inside a ``tempfile.TemporaryDirectory``
per ADR-0026 D.2.
"""

import os
import tempfile
from unittest import TestCase

from pdip.configuration.models.application import ApplicationConfig
from pdip.io.folder_manager import FolderManager


def _build_manager(root_directory):
    config = ApplicationConfig(root_directory=root_directory, name="test")
    return FolderManager(application_config=config)


class CreateFolderIfNotExistCreatesMissingDirectories(TestCase):
    def test_folder_is_created_on_disk_when_it_does_not_exist(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp)
            target = os.path.join(tmp, "new", "nested")

            # Act
            manager.create_folder_if_not_exist(target)

            # Assert
            self.assertTrue(os.path.isdir(target))

    def test_existing_folder_is_left_in_place(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp)
            target = os.path.join(tmp, "already_here")
            os.mkdir(target)
            marker = os.path.join(target, "keep.txt")
            with open(marker, "w", encoding="utf-8") as fh:
                fh.write("keep me")

            # Act
            manager.create_folder_if_not_exist(target)

            # Assert
            self.assertTrue(os.path.isdir(target))
            self.assertTrue(os.path.isfile(marker))
            with open(marker, "r", encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "keep me")


class CopytreeCopiesFilesAndNestedDirectoriesToDestination(TestCase):
    def test_flat_and_nested_content_copied_preserving_file_bytes(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp)
            src = os.path.join(tmp, "src")
            dst = os.path.join(tmp, "dst")
            os.makedirs(os.path.join(src, "sub"))
            os.makedirs(dst)
            with open(os.path.join(src, "top.txt"), "w") as fh:
                fh.write("top")
            with open(os.path.join(src, "sub", "nested.txt"), "w") as fh:
                fh.write("nested")

            # Act
            manager.copytree(src, dst)

            # Assert
            with open(os.path.join(dst, "top.txt"), "r") as fh:
                self.assertEqual(fh.read(), "top")
            with open(os.path.join(dst, "sub", "nested.txt"), "r") as fh:
                self.assertEqual(fh.read(), "nested")


class GetOldFolderPathBuildsUniqueSuffix(TestCase):
    def test_appends_old_suffix_when_target_does_not_exist(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp)
            base = os.path.join(tmp, "data")

            # Act
            result = manager.get_old_folder_path(base)

            # Assert
            self.assertEqual(result, base + "_old")

    def test_recurses_with_numeric_suffix_when_old_slot_is_taken(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp)
            base = os.path.join(tmp, "data")
            os.mkdir(base + "_old")

            # Act
            result = manager.get_old_folder_path(base)

            # Assert
            # The recursion appends a ``1`` to the original name before
            # retrying, yielding ``<base>1_old``.
            self.assertEqual(result, base + "1_old")


class StartCopyMovesFolderIntoOldBackup(TestCase):
    def test_start_copy_creates_backup_when_source_exists(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp)
            folder_name = "project"
            src = os.path.join(tmp, folder_name)
            os.mkdir(src)
            with open(os.path.join(src, "file.txt"), "w") as fh:
                fh.write("payload")

            # Act
            manager.start_copy(folder_name)

            # Assert
            backup = src + "_old"
            self.assertTrue(os.path.isdir(backup))
            with open(os.path.join(backup, "file.txt"), "r") as fh:
                self.assertEqual(fh.read(), "payload")
            # Original folder is left untouched (copy, not move).
            self.assertTrue(os.path.isfile(os.path.join(src, "file.txt")))

    def test_start_copy_is_a_no_op_when_source_missing(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp)

            # Act
            manager.start_copy("does_not_exist")

            # Assert
            # Nothing was created inside the tempdir.
            self.assertEqual(os.listdir(tmp), [])
