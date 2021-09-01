import os
import unittest
from unittest import mock

from dayz_dev_tools import script_logs


class TestNewest(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        listdir_patcher = mock.patch("os.listdir")
        self.mock_listdir = listdir_patcher.start()
        self.addCleanup(listdir_patcher.stop)

        lstat_patcher = mock.patch("os.lstat")
        self.mock_lstat = lstat_patcher.start()
        self.addCleanup(lstat_patcher.stop)

    def test_returns_none_if_there_are_no_script_logs(self) -> None:
        self.mock_listdir.return_value = []

        assert script_logs.newest("dir") is None

        self.mock_listdir.assert_called_once_with("dir")

    def test_returns_name_of_script_log_file_with_most_recent_modified_time(self) -> None:
        self.mock_listdir.return_value = [
            "crash_ignored.log",
            "script_1.log",
            "script_ignored.rpt",
            "script_2.log",
            "other_ignored.log",
            "Script_3.LOG"
        ]
        self.mock_lstat.side_effect = [
            mock.Mock(st_mtime=5000),
            mock.Mock(st_mtime=10000),
            mock.Mock(st_mtime=200)
        ]

        assert script_logs.newest("dir") == os.path.join("dir", "script_2.log")

        assert self.mock_lstat.call_count == 3
        self.mock_lstat.assert_has_calls([
            mock.call(os.path.join("dir", "script_1.log")),
            mock.call(os.path.join("dir", "script_2.log")),
            mock.call(os.path.join("dir", "Script_3.LOG"))
        ])
