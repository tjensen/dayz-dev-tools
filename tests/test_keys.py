import os
import unittest
from unittest import mock

from dayz_dev_tools import keys


class TestCopyKeys(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        listdir_patcher = mock.patch("os.listdir")
        self.mock_listdir = listdir_patcher.start()
        self.addCleanup(listdir_patcher.stop)

        makedirs_patcher = mock.patch("os.makedirs")
        self.mock_makedirs = makedirs_patcher.start()
        self.addCleanup(makedirs_patcher.stop)

        copy2_patcher = mock.patch("shutil.copy2")
        self.mock_copy2 = copy2_patcher.start()
        self.addCleanup(copy2_patcher.stop)

    def test_copies_bikey_files_from_source_directory_to_destination_directory(self) -> None:
        self.mock_listdir.return_value = [
            "ignored",
            "file1.bikey",
            "also-ignored",
            "FILE2.BIKEY",
            "another-ignored",
            "file3.bikey",
            "finally-ignored"
        ]

        keys.copy_keys("source", "destination")

        self.mock_listdir.assert_called_once_with("source")

        self.mock_makedirs.assert_called_once_with("destination", exist_ok=True)

        self.mock_copy2.assert_has_calls([
            mock.call(os.path.join("source", "file1.bikey"), "destination"),
            mock.call(os.path.join("source", "FILE2.BIKEY"), "destination"),
            mock.call(os.path.join("source", "file3.bikey"), "destination")
        ])

    def test_does_nothing_if_the_source_directory_does_not_exist(self) -> None:
        self.mock_listdir.side_effect = FileNotFoundError

        keys.copy_keys("source", "destination")

        self.mock_makedirs.assert_not_called()

        self.mock_copy2.assert_not_called()

    def test_raises_for_other_errors(self) -> None:
        self.mock_listdir.side_effect = Exception("other listdir error")

        with self.assertRaises(Exception):
            keys.copy_keys("source", "destination")

    def test_does_nothing_if_the_source_directory_contains_no_bikey_files(self) -> None:
        self.mock_listdir.return_value = [
            "ignored",
            "also-ignored",
            "another-ignored",
            "finally-ignored"
        ]

        keys.copy_keys("source", "destination")

        self.mock_makedirs.assert_not_called()

        self.mock_copy2.assert_not_called()
