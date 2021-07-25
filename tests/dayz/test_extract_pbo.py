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
            extract_pbo.extract_pbo(self.mock_pboreader, [], verbose=False, deobfuscate=False)

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
                verbose=False, deobfuscate=False)

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
                verbose=False, deobfuscate=False)

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
            extract_pbo.extract_pbo(self.mock_pboreader, [], verbose=True, deobfuscate=False)

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
                verbose=True, deobfuscate=False)

        assert mock_print.call_count == 2
        mock_print.assert_has_calls([
            mock.call("Extracting filename.ext"),
            mock.call(f"Extracting {os.path.join('dir1', 'filename.ext')}")
        ])

    def test_deobfuscates_all_obfuscated_files_when_requested(self) -> None:
        mock_open = mock.mock_open()
        mock_files = [
            self.create_mock_file(b"obfuscated1", b"//***\r\n#include \"not-obfuscated1\"\r\n"),
            self.create_mock_file(
                b"obfuscated2",
                b"/*\r\n#pragma \"whatever\"\r\n*/\r\n#include \"not-obfuscated2\"\r\n"),
            self.create_mock_file(b"obfuscated3", b"#include \"not-obfuscated3\"\r\n"),
            self.create_mock_file(b"not-obfuscated1", b"NOT OBFUSCATED CONTENT 1"),
            self.create_mock_file(b"not-obfuscated2", b"NOT OBFUSCATED CONTENT 2"),
            self.create_mock_file(b"not-obfuscated3", b"NOT OBFUSCATED CONTENT 3")
        ]
        self.mock_pboreader.files.return_value = mock_files
        self.mock_pboreader.file.side_effect = mock_files[3:]

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(self.mock_pboreader, [], verbose=False, deobfuscate=True)

        mock_print.assert_not_called()

        assert mock_open.call_count == 3
        mock_open.assert_has_calls([
            mock.call(b"obfuscated1", "wb"),
            mock.call(b"obfuscated2", "wb"),
            mock.call(b"obfuscated3", "wb")
        ], any_order=True)

        mock_open.return_value.__enter__.return_value.write.assert_has_calls([
            mock.call(b"NOT OBFUSCATED CONTENT 1"),
            mock.call(b"NOT OBFUSCATED CONTENT 2"),
            mock.call(b"NOT OBFUSCATED CONTENT 3")
        ])

        assert self.mock_pboreader.file.call_count == 3
        self.mock_pboreader.file.assert_has_calls([
            mock.call(b"not-obfuscated1"),
            mock.call(b"not-obfuscated2"),
            mock.call(b"not-obfuscated3")
        ])

    def test_prints_skipped_files_when_deobfuscating(self) -> None:
        mock_open = mock.mock_open()
        mock_files = [
            self.create_mock_file(b"obfuscated1", b"//***\r\n#include \"not-obfuscated1\"\r\n"),
            self.create_mock_file(
                b"obfuscated2",
                b"/*\r\n#pragma \"whatever\"\r\n*/\r\n#include \"not-obfuscated2\"\r\n"),
            self.create_mock_file(b"not-obfuscated1", b"NOT OBFUSCATED CONTENT 1"),
            self.create_mock_file(b"not-obfuscated2", b"NOT OBFUSCATED CONTENT 2")
        ]
        self.mock_pboreader.files.return_value = mock_files
        self.mock_pboreader.file.side_effect = [
            self.create_mock_file(b"not-obfuscated1", b"NOT OBFUSCATED CONTENT 1"),
            self.create_mock_file(b"not-obfuscated2", b"NOT OBFUSCATED CONTENT 2")
        ]

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(self.mock_pboreader, [], verbose=True, deobfuscate=True)

        assert mock_print.call_count == 4
        mock_print.assert_has_calls([
            mock.call("Extracting obfuscated1"),
            mock.call("Extracting obfuscated2"),
            mock.call("Skipping obfuscation file: not-obfuscated1"),
            mock.call("Skipping obfuscation file: not-obfuscated2")
        ])

    def test_extracts_files_as_is_if_unobfuscated_file_cannot_be_found(self) -> None:
        mock_open = mock.mock_open()
        content = b"//***\r\n#include \"not-obfuscated1\"\r\n"
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"obfuscated1", content)
        ]
        self.mock_pboreader.file.return_value = None

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(self.mock_pboreader, [], verbose=False, deobfuscate=True)

        mock_print.assert_not_called()

        mock_open.assert_called_once_with(b"obfuscated1", "wb")

        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(content)

        self.mock_pboreader.file.assert_called_once_with(b"not-obfuscated1")

    def test_reports_missing_unobfuscated_file_when_verbose_enabled(self) -> None:
        mock_open = mock.mock_open()
        content = b"//***\r\n#include \"not-obfuscated1\"\r\n"
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"obfuscated1", content)
        ]
        self.mock_pboreader.file.return_value = None

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(self.mock_pboreader, [], verbose=True, deobfuscate=True)

        mock_print.assert_has_calls([
            mock.call("Unable to deobfuscate obfuscated1")
        ])

        mock_open.assert_called_once_with(b"obfuscated1", "wb")

        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(content)

        self.mock_pboreader.file.assert_called_once_with(b"not-obfuscated1")

    def test_skips_invalid_obfuscation_files(self) -> None:
        mock_open = mock.mock_open()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"\t\t", b""),
            self.create_mock_file(b"*.*", b""),
            self.create_mock_file(b"obfuscated1", b"//***\r\n#include \"not-obfuscated1\"\r\n"),
            self.create_mock_file(b"file?to-skip", b""),
            self.create_mock_file(b"another-file-to*skip", b""),
            self.create_mock_file(b"yet-another-file\tto-skip", b""),
            self.create_mock_file(b"high-ascii-characters\xccare-also-skipped", b""),
        ]
        self.mock_pboreader.file.return_value = \
            self.create_mock_file(b"not-obfuscated1", b"NOT OBFUSCATED CONTENT 1")

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(self.mock_pboreader, [], verbose=False, deobfuscate=True)

        mock_print.assert_not_called()

        mock_open.assert_called_once_with(b"obfuscated1", "wb")

        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(
            b"NOT OBFUSCATED CONTENT 1"),

        self.mock_pboreader.file.assert_called_once_with(b"not-obfuscated1")