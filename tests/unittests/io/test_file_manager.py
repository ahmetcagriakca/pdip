"""Behavioural tests for ``pdip.io.file_manager``.

All filesystem work happens inside a ``tempfile.TemporaryDirectory``
per ADR-0026 D.2.
"""

import os
import tempfile
from unittest import TestCase

from pdip.configuration.models.application import ApplicationConfig
from pdip.io.file_manager import FileManager


def _build_manager(root_directory):
    config = ApplicationConfig(root_directory=root_directory, name="test")
    return FileManager(application_config=config)


class CheckPathExistJoinsRootFolderAndFile(TestCase):
    def test_returns_true_when_joined_path_exists_on_disk(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp)
            sub = os.path.join(tmp, "reports")
            os.mkdir(sub)
            with open(os.path.join(sub, "daily.txt"), "w") as fh:
                fh.write("ok")

            # Act
            result = manager.check_path_exist("reports", "daily.txt")

            # Assert
            self.assertTrue(result)

    def test_returns_false_when_joined_path_is_absent(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp)

            # Act
            result = manager.check_path_exist("missing", "file.txt")

            # Assert
            self.assertFalse(result)


class CreateFolderIfNotExistCreatesAbsoluteFolder(TestCase):
    def test_creates_folder_at_path_when_missing(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp)
            target = os.path.join(tmp, "brand_new")

            # Act
            manager.create_folder_if_not_exist(target)

            # Assert
            self.assertTrue(os.path.isdir(target))

    def test_leaves_existing_folder_and_its_contents_untouched(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp)
            target = os.path.join(tmp, "exists")
            os.mkdir(target)
            marker = os.path.join(target, "keep.txt")
            with open(marker, "w") as fh:
                fh.write("content")

            # Act
            manager.create_folder_if_not_exist(target)

            # Assert
            self.assertTrue(os.path.isfile(marker))
            with open(marker, "r") as fh:
                self.assertEqual(fh.read(), "content")


class CreateFileWritesTrimmedContentWithExtension(TestCase):
    def test_creates_file_with_default_py_extension_and_trailing_newline(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp)
            folder = os.path.join(tmp, "gen")

            # Act
            manager.create_file(folder, "module", "   print('hi')   ")

            # Assert
            expected_path = os.path.join(folder, "module.py")
            self.assertTrue(os.path.isfile(expected_path))
            with open(expected_path, "r") as fh:
                # .strip() removes outer whitespace; writer appends "\n".
                self.assertEqual(fh.read(), "print('hi')\n")

    def test_honours_explicit_file_extension(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp)
            folder = os.path.join(tmp, "out")

            # Act
            manager.create_file(
                folder, "notes", "hello\nworld", file_extension=".txt"
            )

            # Assert
            expected_path = os.path.join(folder, "notes.txt")
            self.assertTrue(os.path.isfile(expected_path))
            with open(expected_path, "r") as fh:
                self.assertEqual(fh.read(), "hello\nworld\n")

    def test_creates_missing_parent_folder_before_writing(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp)
            folder = os.path.join(tmp, "nested", "deeper")

            # Act
            manager.create_file(folder, "thing", "data", file_extension=".txt")

            # Assert
            self.assertTrue(os.path.isdir(folder))
            with open(os.path.join(folder, "thing.txt"), "r") as fh:
                self.assertEqual(fh.read(), "data\n")
