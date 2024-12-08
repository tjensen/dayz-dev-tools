import os
import pathlib
import tempfile
import unittest
from unittest import mock

import dayz_dev_tools
from dayz_dev_tools import misc
from dayz_dev_tools import pbo

from tests import helpers


main = helpers.call_main(pbo)


class TestMain(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        logging_patcher = mock.patch("dayz_dev_tools.logging_configuration.configure_logging")
        self.mock_configure_logging = logging_patcher.start()
        self.addCleanup(logging_patcher.stop)

        tools_directory_patcher = mock.patch(
            "dayz_dev_tools.tools_directory.tools_directory", return_value=None)
        self.mock_tools_directory = tools_directory_patcher.start()
        self.addCleanup(tools_directory_patcher.stop)

        self.indir = tempfile.TemporaryDirectory()
        self.addCleanup(self.indir.cleanup)

        self.outdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.outdir.cleanup)

        pbo_writer_patcher = mock.patch("dayz_dev_tools.pbo_writer.PBOWriter", autospec=True)
        self.mock_pbo_writer_class = pbo_writer_patcher.start()
        self.addCleanup(pbo_writer_patcher.stop)

        self.mock_pbo_writer = self.mock_pbo_writer_class.return_value

    def test_parses_args_and_creates_pbo(self) -> None:
        mock_open = mock.mock_open()

        with misc.chdir(self.indir.name), mock.patch("builtins.open", mock_open):
            with mock.patch("dayz_dev_tools.misc.chdir") as mock_chdir:
                main([
                    "ignored",
                    "output.pbo"
                ])

        self.mock_configure_logging.assert_called_once_with(debug=False)

        mock_chdir.assert_called_once_with(".")

        self.mock_tools_directory.assert_called_once_with()

        self.mock_pbo_writer_class.assert_called_once_with(cfgconvert=None)

        self.mock_pbo_writer.add_header.assert_called_once_with(
            "dayz-dev-tools",
            "v" + dayz_dev_tools.version + " - https://dayz-dev-tools.readthedocs.io/"),

        self.mock_pbo_writer.add_file.assert_not_called()

        mock_open.assert_called_once_with("output.pbo", "wb")

        self.mock_pbo_writer.write.assert_called_once_with(
            mock_open.return_value.__enter__.return_value)

    def test_adds_specified_files_and_directories_to_pbo(self) -> None:
        pathlib.Path(self.indir.name, "path", "to").mkdir(parents=True)
        pathlib.Path(self.indir.name, "path", "to", "file1.ext").touch()
        pathlib.Path(self.indir.name, "another", "path").mkdir(parents=True)
        pathlib.Path(self.indir.name, "another", "path", "file2.ext").touch()
        pathlib.Path(self.indir.name, "another", "path", "subdir").mkdir(parents=True)
        pathlib.Path(self.indir.name, "another", "path", "subdir", "file3.ext").touch()
        pathlib.Path(self.indir.name, "file4.ext").touch()

        mock_open = mock.mock_open()

        with misc.chdir(self.indir.name), mock.patch("builtins.open", mock_open):
            main([
                "ignored",
                "output.pbo",
                "path/to/file1.ext",
                "another/path",
                "file4.ext"
            ])

        self.mock_configure_logging.assert_called_once_with(debug=False)

        self.mock_pbo_writer_class.assert_called_once_with(cfgconvert=None)

        assert 4 == self.mock_pbo_writer.add_file.call_count
        self.mock_pbo_writer.add_file.assert_has_calls([
            mock.call(pathlib.Path("path", "to", "file1.ext")),
            mock.call(pathlib.Path("another", "path", "file2.ext")),
            mock.call(pathlib.Path("another", "path", "subdir", "file3.ext")),
            mock.call(pathlib.Path("file4.ext"))
        ])

        mock_open.assert_called_once_with("output.pbo", "wb")

        self.mock_pbo_writer.write.assert_called_once_with(
            mock_open.return_value.__enter__.return_value)

    def test_converts_config_cpp_files_when_tools_directory_is_not_none(self) -> None:
        self.mock_tools_directory.return_value = "TOOLS-DIR"

        with mock.patch("builtins.open", mock.mock_open()):
            main([
                "ignored",
                "output.pbo"
            ])

        self.mock_pbo_writer_class.assert_called_once_with(
            cfgconvert=os.path.join("TOOLS-DIR", "bin", "CfgConvert", "CfgConvert.exe"))

    def test_does_not_convert_config_cpp_files_when_no_convert_option_is_specified(self) -> None:
        self.mock_tools_directory.return_value = "TOOLS-DIR"

        with mock.patch("builtins.open", mock.mock_open()):
            main([
                "ignored",
                "-b",
                "output.pbo"
            ])

        self.mock_pbo_writer_class.assert_called_once_with(cfgconvert=None)

    def test_changes_directory_when_specified(self) -> None:
        with misc.chdir(self.indir.name), mock.patch("builtins.open", mock.mock_open()):
            with mock.patch("dayz_dev_tools.misc.chdir") as mock_chdir:
                main([
                    "ignored",
                    "-C", "some/dir",
                    "output.pbo"
                ])

        mock_chdir.assert_called_once_with("some/dir")

    def test_adds_headers_when_specified(self) -> None:
        with misc.chdir(self.indir.name), mock.patch("builtins.open", mock.mock_open()):
            main([
                "ignored",
                "-H", "prefix=PREFIX",
                "--header", "extra=data=stuff=and=things",
                "output.pbo"
            ])

        assert 3 == self.mock_pbo_writer.add_header.call_count
        self.mock_pbo_writer.add_header.assert_has_calls([
            mock.call("prefix", "PREFIX"),
            mock.call("extra", "data=stuff=and=things")
        ])

    def test_rejects_header_if_it_is_missing_an_equals_sign(self) -> None:
        with misc.chdir(self.indir.name), mock.patch("builtins.open", mock.mock_open()), \
                self.assertRaises(SystemExit) as error:
            main([
                "ignored",
                "-H", "HEADER",
                "output.pbo"
            ])

        assert 2 == error.exception.code

    def test_adds_files_matching_glob_when_pattern_argument_is_specified(self) -> None:
        pathlib.Path(self.indir.name, "match1.ext").touch()
        pathlib.Path(self.indir.name, "path", "to").mkdir(parents=True)
        pathlib.Path(self.indir.name, "path", "to", "match2.ext").touch()
        pathlib.Path(self.indir.name, "path", "to", "no-match.dat").touch()
        pathlib.Path(self.indir.name, "another", "path").mkdir(parents=True)
        pathlib.Path(self.indir.name, "another", "path", "match3.ext").touch()
        pathlib.Path(self.indir.name, "another", "path", "subdir.ext").mkdir(parents=True)
        pathlib.Path(self.indir.name, "another", "path", "subdir.ext", "match4.ext").touch()

        with misc.chdir(self.indir.name), mock.patch("builtins.open", mock.mock_open()):
            main([
                "ignored",
                "--pattern", "**/*.ext",
                "output.pbo"
            ])

        assert 4 == self.mock_pbo_writer.add_file.call_count
        self.mock_pbo_writer.add_file.assert_has_calls([
            mock.call(pathlib.Path("match1.ext")),
            mock.call(pathlib.Path("path", "to", "match2.ext")),
            mock.call(pathlib.Path("another", "path", "match3.ext")),
            mock.call(pathlib.Path("another", "path", "subdir.ext", "match4.ext")),
        ], any_order=True)

    @mock.patch("pathlib.Path.glob", autospec=True)
    def test_accepts_patterns_with_absolute_paths(self, mock_glob: mock.Mock) -> None:
        with misc.chdir(self.indir.name), mock.patch("builtins.open", mock.mock_open()):
            main([
                "ignored",
                "--pattern", "/folder/**/*.ext",
                "output.pbo"
            ])

        mock_glob.assert_called_once_with(pathlib.Path("/"), os.path.join("folder", "**", "*.ext"))

    @mock.patch("subprocess.run")
    def test_signs_pbo_file_when_requested(self, mock_run: mock.Mock) -> None:
        self.mock_tools_directory.return_value = "TOOLS-DIR"

        with misc.chdir(self.indir.name), mock.patch("builtins.open", mock.mock_open()):
            main([
                "ignored",
                "-s", "PRIVATE-KEY-FILENAME",
                "output.pbo"
            ])

        mock_run.assert_called_once_with(
            [
                os.path.join("TOOLS-DIR", "bin", "DsUtils", "DSSignFile.exe"),
                "PRIVATE-KEY-FILENAME",
                "output.pbo"
            ],
            check=True)

    @mock.patch("subprocess.run")
    def test_refuses_to_sign_pbo_file_when_tools_directory_is_none(
        self,
        mock_run: mock.Mock
    ) -> None:
        with misc.chdir(self.indir.name), mock.patch("builtins.open", mock.mock_open()), \
                self.assertRaises(SystemExit) as error:
            main([
                "ignored",
                "-s", "PRIVATE-KEY-FILENAME",
                "output.pbo"
            ])

        assert 1 == error.exception.code

        mock_run.assert_not_called()

    def test_enables_debug_logging_when_option_is_specified(self) -> None:
        with mock.patch("builtins.open", mock.mock_open()):
            main([
                "ignored",
                "--debug",
                "output.pbo"
            ])

        self.mock_configure_logging.assert_called_once_with(debug=True)

    def test_raises_systemexit_on_error(self) -> None:
        self.mock_pbo_writer_class.side_effect = Exception("error message")

        with mock.patch("builtins.open", mock.mock_open()):
            with self.assertRaises(SystemExit) as error:
                main([
                    "ignored",
                    "output.pbo"
                ])

        assert error.exception.code == 1
