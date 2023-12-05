import os
import typing
import unittest
from unittest import mock

from dayz_dev_tools import extract_pbo
from dayz_dev_tools import pbo_file


class TestExtractPbo(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mock_pboreader = mock.Mock()
        self.mock_pboreader.prefix.return_value = None

        makedirs_patcher = mock.patch("os.makedirs")
        self.mock_makedirs = makedirs_patcher.start()
        self.addCleanup(makedirs_patcher.stop)

        bin_to_cpp_patcher = mock.patch("dayz_dev_tools.config_cpp.bin_to_cpp")
        self.mock_bin_to_cpp = bin_to_cpp_patcher.start()
        self.addCleanup(bin_to_cpp_patcher.stop)

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
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=False, deobfuscate=False, cfgconvert=None)

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
            mock.call(os.path.join(b"dir1", b"dir2", b"filename.ext"), "w+b"),
            mock.call(os.path.join(b"dir1", b"filename.ext"), "w+b"),
            mock.call(os.path.join(b"dir1", b"dir2", b"dir3", b"filename.ext"), "w+b"),
            mock.call(os.path.join(b"filename.ext"), "w+b"),
            mock.call(os.path.join(b"other-filename.png"), "w+b")
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
                verbose=False, deobfuscate=False, cfgconvert=None)

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
            mock.call(os.path.join(b"filename.ext"), "w+b"),
            mock.call(os.path.join(b"dir1", b"filename.ext"), "w+b")
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
                verbose=False, deobfuscate=False, cfgconvert=None)

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
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=True, deobfuscate=False, cfgconvert=None)

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
                verbose=True, deobfuscate=False, cfgconvert=None)

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
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=False, deobfuscate=True, cfgconvert=None)

        mock_print.assert_not_called()

        assert mock_open.call_count == 3
        mock_open.assert_has_calls([
            mock.call(b"obfuscated1", "w+b"),
            mock.call(b"obfuscated2", "w+b"),
            mock.call(b"obfuscated3", "w+b")
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

    def test_deobfuscates_obfuscated_files_when_target_file_does_not_have_prefix(self) -> None:
        mock_open = mock.mock_open()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"obfuscated", b"#include \"not-obfuscated\"\r\n"),
        ]
        self.mock_pboreader.file.return_value = \
            self.create_mock_file(b"PREFIX\\not-obfuscated", b"NOT OBFUSCATED CONTENT")
        self.mock_pboreader.prefix.return_value = b"PREFIX"

        with mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=False, deobfuscate=True, cfgconvert=None)

        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(
            b"NOT OBFUSCATED CONTENT"),

        self.mock_pboreader.file.assert_called_once_with(b"PREFIX\\not-obfuscated")

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
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=True, deobfuscate=True, cfgconvert=None)

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
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=False, deobfuscate=True, cfgconvert=None)

        mock_print.assert_not_called()

        mock_open.assert_called_once_with(b"obfuscated1", "w+b")

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
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=True, deobfuscate=True, cfgconvert=None)

        mock_print.assert_has_calls([
            mock.call("Unable to deobfuscate obfuscated1")
        ])

        mock_open.assert_called_once_with(b"obfuscated1", "w+b")

        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(content)

        self.mock_pboreader.file.assert_called_once_with(b"not-obfuscated1")

    def test_skips_invalid_obfuscation_files(self) -> None:
        mock_open = mock.mock_open()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"\t\t", b""),
            self.create_mock_file(b"*.*", b""),
            self.create_mock_file(b"", b""),
            self.create_mock_file(b"\\\\\\", b""),
            self.create_mock_file(b"obfuscated1", b"//***\r\n#include \"not-obfuscated1\"\r\n"),
            self.create_mock_file(b"file?to-skip", b""),
            self.create_mock_file(b"another-file-to*skip", b""),
            self.create_mock_file(b"yet-another-file\tto-skip", b""),
            self.create_mock_file(b"high-ascii-characters\xccare-also-skipped", b""),
        ]
        self.mock_pboreader.file.return_value = \
            self.create_mock_file(b"not-obfuscated1", b"NOT OBFUSCATED CONTENT 1")

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=False, deobfuscate=True, cfgconvert=None)

        mock_print.assert_has_calls([
            mock.call("Skipping empty obfuscation filename"),
            mock.call("Skipping empty obfuscation filename")
        ])

        mock_open.assert_called_once_with(b"obfuscated1", "w+b")

        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(
            b"NOT OBFUSCATED CONTENT 1"),

        self.mock_pboreader.file.assert_called_once_with(b"not-obfuscated1")

    def test_renames_script_files_with_obfuscated_filenames_when_deobfuscating(self) -> None:
        mock_open = mock.mock_open()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"dir\\obfus\xcccated.c", b"contents1"),
            self.create_mock_file(b"dir\\trashy?file.c", b"contents2"),
            self.create_mock_file(b"dir\\gar\tbage.c", b"contents3")
        ]

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=False, deobfuscate=True, cfgconvert=None)

        mock_print.assert_not_called()

        assert mock_open.call_count == 3
        mock_open.assert_has_calls([
            mock.call(os.path.join(b"dir", b"deobfs00000.c"), "w+b"),
            mock.call(os.path.join(b"dir", b"deobfs00001.c"), "w+b"),
            mock.call(os.path.join(b"dir", b"deobfs00002.c"), "w+b")
        ], any_order=True)

        mock_open.return_value.__enter__.return_value.write.assert_has_calls([
            mock.call(b"contents1"),
            mock.call(b"contents2"),
            mock.call(b"contents3")
        ])

    def test_does_not_rename_obfuscated_filenames_when_not_deobfuscating(self) -> None:
        mock_open = mock.mock_open()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"dir\\obfus\xcccated.c", b"contents1"),
            self.create_mock_file(b"dir\\trashy?file.c", b"contents2"),
            self.create_mock_file(b"dir\\gar\tbage.c", b"contents3")
        ]

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=False, deobfuscate=False, cfgconvert=None)

        mock_print.assert_not_called()

        assert mock_open.call_count == 3
        mock_open.assert_has_calls([
            mock.call(os.path.join(b"dir", b"obfus\xcccated.c"), "w+b"),
            mock.call(os.path.join(b"dir", b"trashy?file.c"), "w+b"),
            mock.call(os.path.join(b"dir", b"gar\tbage.c"), "w+b")
        ], any_order=True)

    def test_prints_renamed_script_files_when_verbose_is_true(self) -> None:
        mock_open = mock.mock_open()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"dir\\obfus\xcccated.c", b"contents1"),
            self.create_mock_file(b"dir\\trashy?file.c", b"contents2"),
            self.create_mock_file(b"dir\\gar\tbage.c", b"contents3")
        ]

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=True, deobfuscate=True, cfgconvert=None)

        mock_print.assert_has_calls([
            mock.call(
                "Extracting " + os.path.join('dir', 'obfus\ufffdcated.c')
                + f" -> {os.path.join('dir', 'deobfs00000.c')}"),
            mock.call(
                "Extracting " + os.path.join('dir', 'trashy?file.c')
                + f" -> {os.path.join('dir', 'deobfs00001.c')}"),
            mock.call(
                "Extracting " + os.path.join('dir', 'gar\tbage.c')
                + f" -> {os.path.join('dir', 'deobfs00002.c')}")
        ])

    def test_does_not_convert_config_bin_files_when_cfgconvert_is_none(self) -> None:
        mock_open = mock.mock_open()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"dir1\\config.bin", b"1111")
        ]

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=False, deobfuscate=False, cfgconvert=None)

        mock_print.assert_not_called()

        self.mock_bin_to_cpp.assert_not_called()

        mock_open.assert_called_once_with(os.path.join(b"dir1", b"config.bin"), "w+b")

        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(b"1111")

    def test_converts_config_bin_files_when_cfgconvert_is_not_none(self) -> None:
        self.mock_bin_to_cpp.return_value = b"CPP-CONTENT"
        mock_open = mock.mock_open()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"dir1\\config.bin", b"1111")
        ]

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=False, deobfuscate=False,
                cfgconvert="cppconvert.exe")

        mock_print.assert_not_called()

        self.mock_bin_to_cpp.assert_called_once_with(b"1111", "cppconvert.exe")

        mock_open.assert_called_once_with(os.path.join("dir1", "config.cpp"), "w+b")

        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(b"CPP-CONTENT")

    def test_finds_config_bin_files_case_insensitively(self) -> None:
        self.mock_bin_to_cpp.return_value = b"CPP-CONTENT"
        mock_open = mock.mock_open()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"dir1\\Config.BIN", b"1111")
        ]

        with mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=False, deobfuscate=False,
                cfgconvert="cppconvert.exe")

        self.mock_bin_to_cpp.assert_called_once_with(b"1111", "cppconvert.exe")

        mock_open.assert_called_once_with(os.path.join("dir1", "config.cpp"), "w+b")

    def test_extracts_unconverted_config_bin_if_convert_to_config_cpp_fails(self) -> None:
        self.mock_bin_to_cpp.side_effect = Exception("cfgconvert error")
        mock_open = mock.mock_open()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"dir1\\config.bin", b"1111")
        ]

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=False, deobfuscate=False,
                cfgconvert="cppconvert.exe")

        mock_print.assert_called_once_with(
            f"Failed to convert {os.path.join('dir1', 'config.bin')}: cfgconvert error")

        self.mock_bin_to_cpp.assert_called_once_with(b"1111", "cppconvert.exe")

        mock_open.assert_called_once_with(os.path.join(b"dir1", b"config.bin"), "w+b")

        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(b"1111")

    def test_prints_when_converting_config_bin_files(self) -> None:
        self.mock_bin_to_cpp.return_value = b"CPP-CONTENT"
        mock_open = mock.mock_open()
        self.mock_pboreader.files.return_value = [
            self.create_mock_file(b"dir1\\config.bin", b"1111")
        ]

        with mock.patch("builtins.print") as mock_print, mock.patch("builtins.open", mock_open):
            extract_pbo.extract_pbo(
                self.mock_pboreader, [], verbose=True, deobfuscate=False,
                cfgconvert="cppconvert.exe")

        mock_print.assert_called_once_with(
            f"Converting {os.path.join('dir1', 'config.bin')}"
            f" -> {os.path.join('dir1', 'config.cpp')}")
