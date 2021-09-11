import unittest
from unittest import mock

from dayz_dev_tools import misc


class TestChdir(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        getcwd_patcher = mock.patch("os.getcwd")
        self.mock_getcwd = getcwd_patcher.start()
        self.addCleanup(getcwd_patcher.stop)

        chdir_patcher = mock.patch("os.chdir")
        self.mock_chdir = chdir_patcher.start()
        self.addCleanup(chdir_patcher.stop)

    def test_changes_directory_when_entering_context_and_restores_directory_when_exiting(
        self
    ) -> None:
        self.mock_getcwd.return_value = "old/dir"
        entered = False

        with misc.chdir("new/dir"):
            entered = True

            self.mock_getcwd.assert_called_once_with()

            self.mock_chdir.assert_called_once_with("new/dir")

        assert entered is True

        assert self.mock_chdir.call_count == 2

        self.mock_chdir.assert_called_with("old/dir")

    def test_enters_context_without_changing_directory_when_path_is_none(self) -> None:
        entered = False

        with misc.chdir(None):
            entered = True

            self.mock_getcwd.assert_not_called()

            self.mock_chdir.assert_not_called()

        assert entered is True

        self.mock_chdir.assert_not_called()
