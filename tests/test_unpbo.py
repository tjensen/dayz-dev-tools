import unittest
from unittest import mock

import unpbo


class TestMain(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        extract_pbo_patcher = mock.patch("dayz.extract_pbo.extract_pbo")
        self.mock_extract_pbo = extract_pbo_patcher.start()
        self.addCleanup(extract_pbo_patcher.stop)

        list_pbo_patcher = mock.patch("dayz.list_pbo.list_pbo")
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

        self.mock_extract_pbo.assert_called_once_with(
            self.mock_pboreader, [], verbose=False, deobfuscate=False)

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
            self.mock_pboreader, ["file/to/extract/1", "file/to/extract/2", "file/to/extract/3"],
            verbose=False, deobfuscate=False)

        self.mock_list_pbo.assert_not_called()

    def test_extracts_files_verbosely_when_requested(self) -> None:
        mock_open = mock.mock_open()
        with mock.patch("builtins.open", mock_open):
            unpbo.main([
                "ignored",
                "-v",
                "path/to/filename.ext"
            ])

        self.mock_extract_pbo.assert_called_once_with(
            self.mock_pboreader, [], verbose=True, deobfuscate=False)

        self.mock_list_pbo.assert_not_called()

    def test_deobfuscates_files_while_extracting_them_when_requested(self) -> None:
        mock_open = mock.mock_open()
        with mock.patch("builtins.open", mock_open):
            unpbo.main([
                "ignored",
                "-d",
                "path/to/filename.ext"
            ])

        self.mock_extract_pbo.assert_called_once_with(
            self.mock_pboreader, [], verbose=False, deobfuscate=True)

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
