import os
import typing
import unittest
from unittest import mock

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
        filename = os.path.join("path", "to", "basename.pbo")

        mock_open = mock.mock_open()
        with mock.patch("builtins.open", mock_open):
            unpbo.main([
                "ignored",
                filename
            ])

        mock_open.assert_called_once_with(filename, "rb")

        self.mock_pboreader_class.assert_called_once_with(
            mock_open.return_value.__enter__.return_value)

        self.mock_extract_pbo.assert_called_once_with(self.mock_pboreader, "basename")

        self.mock_list_pbo.assert_not_called()

    def test_extracts_to_specified_directory(self) -> None:
        output_path = os.path.join("output", "dir")

        mock_open = mock.mock_open()
        with mock.patch("builtins.open", mock_open):
            unpbo.main([
                "ignored",
                "INPUT.pbo",
                output_path
            ])

        self.mock_extract_pbo.assert_called_once_with(self.mock_pboreader, output_path)

        self.mock_list_pbo.assert_not_called()

    def test_lists_the_pbo_contents_when_specified(self) -> None:
        mock_open = mock.mock_open()
        with mock.patch("builtins.open", mock_open):
            unpbo.main([
                "ignored",
                "-l",
                "INPUT.pbo"
            ])

        self.mock_list_pbo.assert_called_once_with(self.mock_pboreader)

        self.mock_extract_pbo.assert_not_called()


class TestExtractPbo(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mock_pboreader = mock.Mock()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"dir1\\dir2\\filename.ext", b"1111"),
            self.create_mock_file(b"dir1\\filename.ext", b"2222"),
            self.create_mock_file(b"dir1\\dir2\\dir3\\filename.ext", b"3333"),
            self.create_mock_file(b"filename.ext", b"4444"),
            self.create_mock_file(b"other-filename.png", b"5555")
        ]

    def create_mock_file(self, filename: bytes, contents: bytes) -> mock.Mock:
        def unpack(dest: typing.BinaryIO) -> None:
            dest.write(contents)

        mock_file = mock.Mock(filename=filename)
        mock_file.unpack.side_effect = unpack

        return mock_file

    @mock.patch("os.makedirs")
    def test_extracts_all_files_in_the_pbo_to_destination_directory(
        self, mock_makedirs: mock.Mock
    ) -> None:
        mock_open = mock.mock_open()

        with mock.patch("builtins.open", mock_open):
            unpbo.extract_pbo(self.mock_pboreader, "dest")

        assert mock_makedirs.call_count == 5
        mock_makedirs.assert_has_calls([
            mock.call(os.path.join(b"dest", b"dir1", b"dir2"), exist_ok=True),
            mock.call(os.path.join(b"dest", b"dir1"), exist_ok=True),
            mock.call(os.path.join(b"dest", b"dir1", b"dir2", b"dir3"), exist_ok=True),
            mock.call(os.path.join(b"dest", b""), exist_ok=True),
            mock.call(os.path.join(b"dest", b""), exist_ok=True)
        ])

        assert mock_open.call_count == 5
        mock_open.assert_has_calls([
            mock.call(os.path.join(b"dest", b"dir1", b"dir2", b"filename.ext"), "wb"),
            mock.call(os.path.join(b"dest", b"dir1", b"filename.ext"), "wb"),
            mock.call(os.path.join(b"dest", b"dir1", b"dir2", b"dir3", b"filename.ext"), "wb"),
            mock.call(os.path.join(b"dest", b"filename.ext"), "wb"),
            mock.call(os.path.join(b"dest", b"other-filename.png"), "wb")
        ], any_order=True)

        mock_open.return_value.__enter__.return_value.write.assert_has_calls([
            mock.call(b"1111"),
            mock.call(b"2222"),
            mock.call(b"3333"),
            mock.call(b"4444"),
            mock.call(b"5555")
        ])


class TestListPbo(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mock_pboreader = mock.Mock()
        self.mock_pboreader.files.return_value = [
            mock.Mock(filename=b"dir1\\dir2\\filename.ext"),
            mock.Mock(filename=b"dir1\\filename.ext"),
            mock.Mock(filename=b"dir1\\dir2\\dir3\\filename.ext"),
            mock.Mock(filename=b"filename.ext"),
            mock.Mock(filename=b"other-filename.png")
        ]

    def test_prints_the_filenames_of_files_in_the_pbo(self) -> None:
        with mock.patch("builtins.print") as mock_print:
            unpbo.list_pbo(self.mock_pboreader)

        assert mock_print.call_count == 5

        mock_print.assert_has_calls([
            mock.call("dir1\\dir2\\filename.ext"),
            mock.call("dir1\\filename.ext"),
            mock.call("dir1\\dir2\\dir3\\filename.ext"),
            mock.call("filename.ext"),
            mock.call("other-filename.png")
        ])

    def test_replaces_unknown_characters_in_filenames(self) -> None:
        self.mock_pboreader.files.return_value = [
            mock.Mock(filename=b"dir1\\dir2\\file\x88name.wss")
        ]

        with mock.patch("builtins.print") as mock_print:
            unpbo.list_pbo(self.mock_pboreader)

        mock_print.assert_called_once_with("dir1\\dir2\\file\ufffdname.wss")
