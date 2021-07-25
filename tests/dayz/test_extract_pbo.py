import os
import typing
import unittest
from unittest import mock

from dayz import extract_pbo
from dayz import pbo_file


class TestExtractPbo(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mock_pboreader = mock.Mock()

        makedirs_patcher = mock.patch("os.makedirs")
        self.mock_makedirs = makedirs_patcher.start()
        self.addCleanup(makedirs_patcher.stop)

    def create_mock_file(self, filename: bytes, contents: bytes) -> pbo_file.PBOFile:
        def unpack(dest: typing.BinaryIO) -> None:
            dest.write(contents)

        mock_file = pbo_file.PBOFile(filename, b"", 0, 0, 0, 0)
        mock.patch.object(mock_file, "unpack", side_effect=unpack).start()

        return mock_file

    def test_extracts_all_files_in_the_pbo(self) -> None:
        mock_open = mock.mock_open()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"dir1\\dir2\\filename.ext", b"1111"),
            self.create_mock_file(b"dir1\\filename.ext", b"2222"),
            self.create_mock_file(b"dir1\\dir2\\dir3\\filename.ext", b"3333"),
            self.create_mock_file(b"filename.ext", b"4444"),
            self.create_mock_file(b"other-filename.png", b"5555")
        ]

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(self.mock_pboreader, [], verbose=False)

        mock_print.assert_not_called()

        self.mock_pboreader.files.assert_called_once_with()

        assert self.mock_makedirs.call_count == 3
        self.mock_makedirs.assert_has_calls([
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

    def test_extracts_specified_files_when_provided(self) -> None:
        mock_open = mock.mock_open()
        self.mock_pboreader.file.side_effect = [
            self.create_mock_file(b"filename.ext", b"4444"),
            self.create_mock_file(b"dir1\\filename.ext", b"2222")
        ]

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(
                self.mock_pboreader,
                [
                    os.path.join("filename.ext"),
                    os.path.join("dir1", "filename.ext")
                ],
                verbose=False)

        mock_print.assert_not_called()

        assert self.mock_pboreader.file.call_count == 2
        self.mock_pboreader.file.assert_has_calls([
            mock.call(os.path.join("filename.ext")),
            mock.call(os.path.join("dir1", "filename.ext"))
        ])

        assert self.mock_makedirs.call_count == 1
        self.mock_makedirs.assert_called_once_with(b"dir1", exist_ok=True)

        assert mock_open.call_count == 2
        mock_open.assert_has_calls([
            mock.call(os.path.join(b"filename.ext"), "wb"),
            mock.call(os.path.join(b"dir1", b"filename.ext"), "wb")
        ], any_order=True)

        mock_open.return_value.__enter__.return_value.write.assert_has_calls([
            mock.call(b"4444"),
            mock.call(b"2222")
        ])

    def test_raises_if_specified_filename_does_not_exist(self) -> None:
        self.mock_pboreader.file.return_value = None

        with self.assertRaises(Exception):
            extract_pbo.extract_pbo(
                self.mock_pboreader,
                [
                    os.path.join("filename.ext"),
                    os.path.join("dir1", "filename.ext")
                ],
                verbose=False)

        self.mock_pboreader.file.assert_called_once()

        self.mock_makedirs.assert_not_called()

    def test_prints_filenames_as_they_are_extracted_when_verbose_is_true(self) -> None:
        mock_open = mock.mock_open()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"dir1\\dir2\\filename.ext", b"1111"),
            self.create_mock_file(b"dir1\\filename.ext", b"2222"),
            self.create_mock_file(b"dir1\\dir2\\dir3\\filename.ext", b"3333"),
            self.create_mock_file(b"filename.ext", b"4444"),
            self.create_mock_file(b"other-filename.png", b"5555")
        ]

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(self.mock_pboreader, [], verbose=True)

        assert mock_print.call_count == 5
        mock_print.assert_has_calls([
            mock.call(f"Extracting {os.path.join('dir1', 'dir2', 'filename.ext')}"),
            mock.call(f"Extracting {os.path.join('dir1', 'filename.ext')}"),
            mock.call(f"Extracting {os.path.join('dir1', 'dir2', 'dir3', 'filename.ext')}"),
            mock.call("Extracting filename.ext"),
            mock.call("Extracting other-filename.png")
        ])

    def test_prints_specified_filenames_as_they_are_extracted_when_verbose_is_true(self) -> None:
        mock_open = mock.mock_open()
        self.mock_pboreader.file.side_effect = [
            self.create_mock_file(b"filename.ext", b"4444"),
            self.create_mock_file(b"dir1\\filename.ext", b"2222")
        ]

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(
                self.mock_pboreader,
                [
                    os.path.join("filename.ext"),
                    os.path.join("dir1", "filename.ext")
                ],
                verbose=True)

        assert mock_print.call_count == 2
        mock_print.assert_has_calls([
            mock.call("Extracting filename.ext"),
            mock.call(f"Extracting {os.path.join('dir1', 'filename.ext')}")
        ])
