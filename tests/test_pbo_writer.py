import io
import pathlib
import unittest
from unittest import mock

from dayz_dev_tools import pbo_writer


class TestPBOWriter(unittest.TestCase):
    def test_write_creates_empty_pbo_file(self) -> None:
        output = io.BytesIO()

        writer = pbo_writer.PBOWriter(cfgconvert="path/to/cfgconvert.exe")
        writer.write(output)

        assert b"\x00sreV" + (b"\x00" * 38) == output.getvalue()

    def test_add_header_includes_added_header_in_written_pbo_file(self) -> None:
        output = io.BytesIO()

        writer = pbo_writer.PBOWriter(cfgconvert="path/to/cfgconvert.exe")
        writer.add_header("NAME", "VALUE")
        writer.write(output)

        assert b"NAME\x00VALUE\x00\x00" + (b"\x00" * 21) == output.getvalue()[21:]

    def test_add_header_accepts_values_as_bytes(self) -> None:
        output = io.BytesIO()

        writer = pbo_writer.PBOWriter(cfgconvert="path/to/cfgconvert.exe")
        writer.add_header(b"NAME", b"VALUE")
        writer.write(output)

        assert b"NAME\x00VALUE\x00\x00" + (b"\x00" * 21) == output.getvalue()[21:]

    @mock.patch.object(pathlib.Path, "stat")
    def test_add_file_includes_added_file_in_written_pbo_file(self, mock_stat: mock.Mock) -> None:
        output = io.BytesIO()
        mock_open = mock.mock_open()
        mock_open.return_value.__enter__.return_value.read.return_value = b"FILE-CONTENTS"

        mock_stat.return_value.st_size = 13
        mock_stat.return_value.st_mtime = 305419896.567

        path = pathlib.Path("PATH/TO/FILENAME")

        with mock.patch("builtins.open", mock_open):
            writer = pbo_writer.PBOWriter(cfgconvert="path/to/cfgconvert.exe")
            writer.add_file(path)
            writer.write(output)

        mock_stat.assert_called_once_with()

        mock_open.assert_called_once_with(path, "rb")

        assert b"PATH\\TO\\FILENAME\x00\x00\x00\x00\x00\x0d\x00\x00\x00\x00\x00\x00\x00" \
            b"\x78\x56\x34\x12\x0d\x00\x00\x00" + (b"\x00" * 21) + b"FILE-CONTENTS" \
            == output.getvalue()[22:]

    @mock.patch.object(pathlib.Path, "stat")
    def test_add_file_removes_anchor_from_filename(self, mock_stat: mock.Mock) -> None:
        output = io.BytesIO()
        mock_open = mock.mock_open()
        mock_open.return_value.__enter__.return_value.read.return_value = b"FILE-CONTENTS"

        mock_stat.return_value.st_size = 13
        mock_stat.return_value.st_mtime = 305419896.567

        path = pathlib.Path("C:/PATH/TO/FILENAME")

        with mock.patch("builtins.open", mock_open):
            writer = pbo_writer.PBOWriter(cfgconvert="path/to/cfgconvert.exe")
            writer.add_file(path)
            writer.write(output)

        assert b"PATH\\TO\\FILENAME\x00" == output.getvalue()[22:39]

    @mock.patch.object(pathlib.Path, "stat")
    @mock.patch("dayz_dev_tools.config_cpp.cpp_to_bin")
    def test_add_file_converts_config_cpp_to_config_bin(
        self,
        mock_cpp_to_bin: mock.Mock,
        mock_stat: mock.Mock
    ) -> None:
        mock_cpp_to_bin.return_value = b"BIN-CONTENTS"

        output = io.BytesIO()
        mock_open = mock.mock_open()
        mock_open.return_value.__enter__.return_value.read.return_value = b"FILE-CONTENTS"

        mock_stat.return_value.st_size = 13
        mock_stat.return_value.st_mtime = 305419896.567

        path = pathlib.Path("path/to/ConFig.cPp")

        with mock.patch("builtins.open", mock_open):
            writer = pbo_writer.PBOWriter(cfgconvert="path/to/cfgconvert.exe")
            writer.add_file(path)
            writer.write(output)

        mock_cpp_to_bin.assert_called_once_with(b"FILE-CONTENTS", "path/to/cfgconvert.exe")

        assert b"path\\to\\ConFig.bin\x00\x00\x00\x00\x00\x0c\x00\x00\x00\x00\x00\x00\x00" \
            b"\x78\x56\x34\x12\x0c\x00\x00\x00" + (b"\x00" * 21) + b"BIN-CONTENTS" \
            == output.getvalue()[22:]

    @mock.patch.object(pathlib.Path, "stat")
    def test_add_file_does_not_convert_config_cpp_if_cfgconvert_is_none(
        self,
        mock_stat: mock.Mock
    ) -> None:
        output = io.BytesIO()
        mock_open = mock.mock_open()
        mock_open.return_value.__enter__.return_value.read.return_value = b"FILE-CONTENTS"

        mock_stat.return_value.st_size = 13
        mock_stat.return_value.st_mtime = 305419896.567

        path = pathlib.Path("path/to/config.cpp")

        with mock.patch("builtins.open", mock_open):
            writer = pbo_writer.PBOWriter(cfgconvert=None)
            writer.add_file(path)
            writer.write(output)

        mock_stat.assert_called_once_with()

        mock_open.assert_called_once_with(path, "rb")

        assert b"path\\to\\config.cpp\x00\x00\x00\x00\x00\x0d\x00\x00\x00\x00\x00\x00\x00" \
            b"\x78\x56\x34\x12\x0d\x00\x00\x00" + (b"\x00" * 21) + b"FILE-CONTENTS" \
            == output.getvalue()[22:]
