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


class TestWaitForNew(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        newest_patcher = mock.patch("dayz_dev_tools.script_logs.newest")
        self.mock_newest = newest_patcher.start()
        self.addCleanup(newest_patcher.stop)

        sleep_patcher = mock.patch("time.sleep")
        self.mock_sleep = sleep_patcher.start()
        self.addCleanup(sleep_patcher.stop)

    def test_waits_until_a_new_script_log_is_created(self) -> None:
        self.mock_newest.side_effect = [
            "script_previous.log",
            "script_previous.log",
            "script_previous.log",
            "script_new.log"
        ]

        assert script_logs.wait_for_new("profile/dir", "script_previous.log") == "script_new.log"

        assert self.mock_newest.call_count == 4
        self.mock_newest.assert_called_with("profile/dir")

        assert self.mock_sleep.call_count == 3
        self.mock_sleep.assert_called_with(1)

    def test_returns_new_log_if_created_before_timeout_expires(self) -> None:
        self.mock_newest.side_effect = ["script_previous.log"] * 9 + ["script_new.log"]

        assert script_logs.wait_for_new("profile/dir", "script_previous.log") == "script_new.log"

        assert self.mock_newest.call_count == 10
        assert self.mock_sleep.call_count == 9

    def test_returns_none_if_no_new_log_is_detected_within_timeout(self) -> None:
        self.mock_newest.side_effect = ["script_previous.log"] * 11

        assert script_logs.wait_for_new("profile/dir", "script_previous.log") is None

        assert self.mock_newest.call_count == 11
        assert self.mock_sleep.call_count == 10

    def test_gives_up_after_specified_timeout(self) -> None:
        self.mock_newest.side_effect = ["script_previous.log"] * 6

        assert script_logs.wait_for_new("profile/dir", "script_previous.log", timeout=5) is None

        assert self.mock_newest.call_count == 6
        assert self.mock_sleep.call_count == 5


class TestStream(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        sleep_patcher = mock.patch("time.sleep")
        self.mock_sleep = sleep_patcher.start()
        self.addCleanup(sleep_patcher.stop)

        self.outfile = mock.Mock()
        self.infile = mock.Mock()
        self.keep_streaming = mock.Mock()

    def test_streams_log_content_to_output_file_until_told_to_stop(self) -> None:
        self.infile.readline.side_effect = [
            "first line\n",
            "",
            "second line\n",
            "",
            "third line\n",
        ]
        self.keep_streaming.side_effect = [
            True, True, True, True, True, False
        ]

        script_logs.stream(self.outfile, self.infile, self.keep_streaming)

        assert self.keep_streaming.call_count == 6
        self.keep_streaming.assert_called_with()

        assert self.infile.readline.call_count == 5
        self.infile.readline.assert_called_with()

        assert self.outfile.write.call_count == 3
        self.outfile.write.assert_has_calls([
            mock.call("first line\n"),
            mock.call("second line\n"),
            mock.call("third line\n"),
        ])

        assert self.mock_sleep.call_count == 2
        self.mock_sleep.assert_called_with(0.5)
