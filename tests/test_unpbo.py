import datetime
import os
import typing
import unittest
from unittest import mock

from dayz import pbo_file
import unpbo


class TestMain(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        extract_pbo_patcher = mock.patch("unpbo.extract_pbo")
        self.mock_extract_pbo = extract_pbo_patcher.start()
        self.addCleanup(extract_pbo_patcher.stop)

        list_pbo_patcher = mock.patch("unpbo.list_pbo")
        self.mock_list_pbo = list_pbo_patcher.start()
        self.addCleanup(list_pbo_patcher.stop)

        pboreader_patcher = mock.patch("dayz.pbo_reader.PBOReader")
        self.mock_pboreader_class = pboreader_patcher.start()
        self.addCleanup(pboreader_patcher.stop)

        self.mock_pboreader = self.mock_pboreader_class.return_value

    def test_parses_args_and_extracts_pbo(self) -> None:
        mock_open = mock.mock_open()
        with mock.patch("builtins.open", mock_open):
            unpbo.main([
                "ignored",
                "path/to/filename.ext"
            ])

        mock_open.assert_called_once_with("path/to/filename.ext", "rb")

        self.mock_pboreader_class.assert_called_once_with(
            mock_open.return_value.__enter__.return_value)

        self.mock_extract_pbo.assert_called_once_with(self.mock_pboreader, [])

        self.mock_list_pbo.assert_not_called()

    def test_extracts_files_specified_on_command_line(self) -> None:
        mock_open = mock.mock_open()
        with mock.patch("builtins.open", mock_open):
            unpbo.main([
                "ignored",
                "path/to/filename.ext",
                "file/to/extract/1",
                "file/to/extract/2",
                "file/to/extract/3"
            ])

        mock_open.assert_called_once_with("path/to/filename.ext", "rb")

        self.mock_pboreader_class.assert_called_once_with(
            mock_open.return_value.__enter__.return_value)

        self.mock_extract_pbo.assert_called_once_with(
            self.mock_pboreader, ["file/to/extract/1", "file/to/extract/2", "file/to/extract/3"])

        self.mock_list_pbo.assert_not_called()

    def test_lists_the_pbo_contents_when_option_is_specified(self) -> None:
        mock_open = mock.mock_open()
        with mock.patch("builtins.open", mock_open):
            unpbo.main([
                "ignored",
                "-l",
                "INPUT.pbo"
            ])

        self.mock_list_pbo.assert_called_once_with(self.mock_pboreader, verbose=False)

        self.mock_extract_pbo.assert_not_called()

    def test_lists_the_pbo_with_verbose_output_when_option_is_specified(self) -> None:
        mock_open = mock.mock_open()
        with mock.patch("builtins.open", mock_open):
            unpbo.main([
                "ignored",
                "-l",
                "-v",
                "INPUT.pbo"
            ])

        self.mock_list_pbo.assert_called_once_with(self.mock_pboreader, verbose=True)

        self.mock_extract_pbo.assert_not_called()


class TestExtractPbo(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mock_pboreader = mock.Mock()

    def create_mock_file(self, filename: bytes, contents: bytes) -> pbo_file.PBOFile:
        def unpack(dest: typing.BinaryIO) -> None:
            dest.write(contents)

        mock_file = pbo_file.PBOFile(filename, b"", 0, 0, 0, 0)
        mock.patch.object(mock_file, "unpack", side_effect=unpack).start()

        return mock_file

    @mock.patch("os.makedirs")
    def test_extracts_all_files_in_the_pbo(self, mock_makedirs: mock.Mock) -> None:
        mock_open = mock.mock_open()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"dir1\\dir2\\filename.ext", b"1111"),
            self.create_mock_file(b"dir1\\filename.ext", b"2222"),
            self.create_mock_file(b"dir1\\dir2\\dir3\\filename.ext", b"3333"),
            self.create_mock_file(b"filename.ext", b"4444"),
            self.create_mock_file(b"other-filename.png", b"5555")
        ]

        with mock.patch("builtins.open", mock_open):
            unpbo.extract_pbo(self.mock_pboreader, [])

        self.mock_pboreader.files.assert_called_once_with()

        assert mock_makedirs.call_count == 3
        mock_makedirs.assert_has_calls([
            mock.call(os.path.join(b"dir1", b"dir2"), exist_ok=True),
            mock.call(os.path.join(b"dir1"), exist_ok=True),
            mock.call(os.path.join(b"dir1", b"dir2", b"dir3"), exist_ok=True)
        ])

        assert mock_open.call_count == 5
        mock_open.assert_has_calls([
            mock.call(os.path.join(b"dir1", b"dir2", b"filename.ext"), "wb"),
            mock.call(os.path.join(b"dir1", b"filename.ext"), "wb"),
            mock.call(os.path.join(b"dir1", b"dir2", b"dir3", b"filename.ext"), "wb"),
            mock.call(os.path.join(b"filename.ext"), "wb"),
            mock.call(os.path.join(b"other-filename.png"), "wb")
        ], any_order=True)

        mock_open.return_value.__enter__.return_value.write.assert_has_calls([
            mock.call(b"1111"),
            mock.call(b"2222"),
            mock.call(b"3333"),
            mock.call(b"4444"),
            mock.call(b"5555")
        ])

    @mock.patch("os.makedirs")
    def test_extracts_specified_files_when_provided(self, mock_makedirs: mock.Mock) -> None:
        mock_open = mock.mock_open()
        self.mock_pboreader.file.side_effect = [
            self.create_mock_file(b"filename.ext", b"4444"),
            self.create_mock_file(b"dir1\\filename.ext", b"2222")
        ]

        with mock.patch("builtins.open", mock_open):
            unpbo.extract_pbo(
                self.mock_pboreader,
                [
                    os.path.join("filename.ext"),
                    os.path.join("dir1", "filename.ext")
                ])

        assert self.mock_pboreader.file.call_count == 2
        self.mock_pboreader.file.assert_has_calls([
            mock.call(os.path.join("filename.ext")),
            mock.call(os.path.join("dir1", "filename.ext"))
        ])

        assert mock_makedirs.call_count == 1
        mock_makedirs.assert_called_once_with(b"dir1", exist_ok=True)

        assert mock_open.call_count == 2
        mock_open.assert_has_calls([
            mock.call(os.path.join(b"filename.ext"), "wb"),
            mock.call(os.path.join(b"dir1", b"filename.ext"), "wb")
        ], any_order=True)

        mock_open.return_value.__enter__.return_value.write.assert_has_calls([
            mock.call(b"4444"),
            mock.call(b"2222")
        ])

    @mock.patch("os.makedirs")
    def test_raises_if_specified_filename_does_not_exist(self, mock_makedirs: mock.Mock) -> None:
        self.mock_pboreader.file.return_value = None

        with self.assertRaises(Exception):
            unpbo.extract_pbo(
                self.mock_pboreader,
                [
                    os.path.join("filename.ext"),
                    os.path.join("dir1", "filename.ext")
                ])

        self.mock_pboreader.file.assert_called_once()

        mock_makedirs.assert_not_called()


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
            unpbo.list_pbo(self.mock_pboreader, verbose=False)

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
            unpbo.list_pbo(self.mock_pboreader, verbose=True)

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
