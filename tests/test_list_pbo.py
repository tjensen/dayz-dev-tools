import datetime
import os
import typing
import unittest
from unittest import mock

from dayz_dev_tools import list_pbo
from dayz_dev_tools import pbo_file


class TestListPbo(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.timestamps = [
            1626130666,
            1519283521,
            1603105281,
            1592848278,
            1617284725
        ]

        self.mock_pboreader = mock.Mock()
        self.mock_pboreader.files.return_value = [
            pbo_file.PBOFile(b"dir1\\dir2\\filename.ext", b"", 10000, 0, self.timestamps[0], 9000),
            pbo_file.PBOFile(b"dir1\\filename.ext", b"ABCD", 234, 0, self.timestamps[1], 200),
            pbo_file.PBOFile(
                b"dir1\\dir2\\dir3\\filename.ext", b"1234", 54321, 0, self.timestamps[2], 50000),
            pbo_file.PBOFile(b"filename.ext", b"\0\0\0\0", 0, 0, self.timestamps[3], 10),
            pbo_file.PBOFile(
                b"other-filename.png", b"\x88\x99\xaa\xbb", 7777, 0, self.timestamps[4], 6000)
        ]
        self.mock_pboreader.headers.return_value = [
            (b"foo", b"bar"),
            (b"other", b"header stuff"),
            (b"\x88\x99\xaa", b"\xbb\xcc\xdd")
        ]

    def create_mock_file(
            self, filename: bytes, original_size: int, data_size: int) -> pbo_file.PBOFile:
        return pbo_file.PBOFile(filename, b"", original_size, 0, 0, data_size)

    def expected_call(self, size: int, timestamp: int, filename: str) -> typing.Any:
        date_time = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
        return mock.call(f"{size:9}  {date_time}  {filename}")

    def expected_verbose_call(
            self, original: int, type: str, size: int, timestamp: int, filename: str) -> typing.Any:
        date_time = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
        return mock.call(f"{original:9}  {type}  {size:9}  {date_time}  {filename}")

    def test_prints_basic_details_of_files_in_the_pbo(self) -> None:
        with mock.patch("builtins.print") as mock_print:
            list_pbo.list_pbo(self.mock_pboreader, verbose=False)

        assert mock_print.call_count == 9

        mock_print.assert_has_calls([
            mock.call(" Original     Date    Time   Name"),
            mock.call("---------  ---------- -----  ----"),
            self.expected_call(
                10000, self.timestamps[0], os.path.join("dir1", "dir2", "filename.ext")),
            self.expected_call(234, self.timestamps[1], os.path.join("dir1", "filename.ext")),
            self.expected_call(
                54321, self.timestamps[2], os.path.join("dir1", "dir2", "dir3", "filename.ext")),
            self.expected_call(10, self.timestamps[3], "filename.ext"),
            self.expected_call(7777, self.timestamps[4], "other-filename.png"),
            mock.call("---------                    ---------"),
            mock.call("    72342                    5 Files")
        ])

    def test_prints_headers_and_extended_details_with_verbose_output(self) -> None:
        with mock.patch("builtins.print") as mock_print:
            list_pbo.list_pbo(self.mock_pboreader, verbose=True)

        assert mock_print.call_count == 15

        mock_print.assert_has_calls([
            mock.call("Headers:"),
            mock.call("--------"),
            mock.call("foo = bar"),
            mock.call("other = header stuff"),
            mock.call("\ufffd\ufffd\ufffd = \ufffd\ufffd\ufffd"),
            mock.call(),
            mock.call(" Original  Type    Size        Date    Time   Name"),
            mock.call("---------  ----  ---------  ---------- -----  ----"),
            self.expected_verbose_call(
                10000, "    ", 9000, self.timestamps[0],
                os.path.join("dir1", "dir2", "filename.ext")),
            self.expected_verbose_call(
                234, "ABCD", 200, self.timestamps[1], os.path.join("dir1", "filename.ext")),
            self.expected_verbose_call(
                54321, "1234", 50000, self.timestamps[2],
                os.path.join("dir1", "dir2", "dir3", "filename.ext")),
            self.expected_verbose_call(10, "    ", 10, self.timestamps[3], "filename.ext"),
            self.expected_verbose_call(
                7777, "    ", 6000, self.timestamps[4], "other-filename.png"),
            mock.call("---------        ---------                    ---------"),
            mock.call("    72342            65210                    5 Files")
        ])
