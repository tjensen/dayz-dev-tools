import os
import unittest
from unittest import mock

from dayz_dev_tools import keys


class TestCopyKeys(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        walk_patcher = mock.patch("os.walk")
        self.mock_walk = walk_patcher.start()
        self.addCleanup(walk_patcher.stop)

        makedirs_patcher = mock.patch("os.makedirs")
        self.mock_makedirs = makedirs_patcher.start()
        self.addCleanup(makedirs_patcher.stop)

        copy2_patcher = mock.patch("shutil.copy2")
        self.mock_copy2 = copy2_patcher.start()
        self.addCleanup(copy2_patcher.stop)

    def test_copies_bikey_files_from_source_directory_to_destination_directory(self) -> None:
        self.mock_walk.return_value = iter([
            ("root1", ["ignored"], ["ignored", "file1.bikey"]),
            ("root2", ["ignored.bikey"], ["also-ignored", "FILE2.BIKEY", "file3.bikey"]),
            ("root3", ["ignored"], ["another-ignored", "file4.bikey", "finally-ignored"])
        ])

        keys.copy_keys("source", "destination")

        self.mock_walk.assert_called_once_with("source")

        self.mock_makedirs.assert_called_once_with("destination", exist_ok=True)

        self.mock_copy2.assert_has_calls([
            mock.call(os.path.join("root1", "file1.bikey"), "destination"),
            mock.call(os.path.join("root2", "FILE2.BIKEY"), "destination"),
            mock.call(os.path.join("root2", "file3.bikey"), "destination"),
            mock.call(os.path.join("root3", "file4.bikey"), "destination")
        ])

    def test_raises_for_other_errors(self) -> None:
        expected_error = Exception("other walk error")
        self.mock_walk.side_effect = expected_error

        with self.assertRaises(Exception) as error:
            keys.copy_keys("source", "destination")

        assert error.exception is expected_error

    def test_does_nothing_if_the_source_directory_contains_no_bikey_files(self) -> None:
        self.mock_walk.return_value = [
            ("root", [], [])
        ]

        keys.copy_keys("source", "destination")

        self.mock_makedirs.assert_not_called()

        self.mock_copy2.assert_not_called()
