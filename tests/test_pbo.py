import pathlib
import tempfile
import unittest
from unittest import mock

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

        self.indir = tempfile.TemporaryDirectory()
        self.addCleanup(self.indir.cleanup)

        self.outdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.outdir.cleanup)

        pbo_writer_patcher = mock.patch("dayz_dev_tools.pbo_writer.PBOWriter", autospec=True)
        self.mock_pbo_writer_class = pbo_writer_patcher.start()
        self.addCleanup(pbo_writer_patcher.stop)

        self.mock_pbo_writer = self.mock_pbo_writer_class.return_value

    def test_parses_args_and_creates_pbo(self) -> None:
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

        self.mock_pbo_writer_class.assert_called_once_with()

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

    def test_adds_headers_when_specified(self) -> None:
        with misc.chdir(self.indir.name), mock.patch("builtins.open", mock.mock_open()):
            main([
                "ignored",
                "-H", "prefix=PREFIX",
                "--header", "extra=data=stuff=and=things",
                "output.pbo"
            ])

        assert 2 == self.mock_pbo_writer.add_header.call_count
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
