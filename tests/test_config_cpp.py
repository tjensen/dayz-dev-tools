import io
import os
import unittest
from unittest import mock

from dayz_dev_tools import config_cpp


class TestBinToCpp(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        temporary_directory_patcher = mock.patch("tempfile.TemporaryDirectory", autospec=True)
        self.mock_temporary_directory_class = temporary_directory_patcher.start()
        self.addCleanup(temporary_directory_patcher.stop)

        self.mock_temporary_directory_context = self.mock_temporary_directory_class.return_value

        open_patcher = mock.patch("builtins.open", mock.mock_open())
        self.mock_open = open_patcher.start()
        self.addCleanup(open_patcher.stop)

        run_patcher = mock.patch("subprocess.run")
        self.mock_run = run_patcher.start()
        self.addCleanup(run_patcher.stop)

    def test_converts_config_bin_to_config_cpp(self) -> None:
        temp_bin_file = io.BytesIO()
        temp_cpp_file = io.BytesIO(b"CPP-CONTENT")

        self.mock_temporary_directory_context.__enter__.return_value = "TEMP-DIR"

        self.mock_open.return_value.__enter__.side_effect = [
            temp_bin_file,
            temp_cpp_file
        ]

        out_content = config_cpp.bin_to_cpp(b"BIN-CONTENT", "path/to/cfgconvert.exe")

        assert out_content == b"CPP-CONTENT"

        self.mock_temporary_directory_class.assert_called_once_with()

        assert self.mock_open.call_count == 2
        assert self.mock_open.call_args_list == [
            mock.call(os.path.join("TEMP-DIR", "config.bin"), "w+b"),
            mock.call(os.path.join("TEMP-DIR", "config.cpp"), "rb")
        ]

        self.mock_run.assert_called_once_with(
            [
                "path/to/cfgconvert.exe",
                "-txt",
                "-dst", os.path.join("TEMP-DIR", "config.cpp"),
                os.path.join("TEMP-DIR", "config.bin")
            ],
            check=True)
