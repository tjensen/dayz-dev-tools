import io
import pathlib
import unittest
from unittest import mock

from dayz_dev_tools import pbo_writer


class TestPBOWriter(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.pbo_writer = pbo_writer.PBOWriter()

    def test_write_creates_empty_pbo_file(self) -> None:
        output = io.BytesIO()

        self.pbo_writer.write(output)

        assert b"\x00sreV" + (b"\x00" * 38) == output.getvalue()

    def test_add_header_includes_added_header_in_written_pbo_file(self) -> None:
        output = io.BytesIO()

        self.pbo_writer.add_header("NAME", "VALUE")
        self.pbo_writer.write(output)

        assert b"NAME\x00VALUE\x00\x00" + (b"\x00" * 21) == output.getvalue()[21:]

    def test_add_header_accepts_values_as_bytes(self) -> None:
        output = io.BytesIO()

        self.pbo_writer.add_header(b"NAME", b"VALUE")
        self.pbo_writer.write(output)

        assert b"NAME\x00VALUE\x00\x00" + (b"\x00" * 21) == output.getvalue()[21:]

    def test_add_file_includes_added_file_in_written_pbo_file(self) -> None:
        output = io.BytesIO()
        mock_open = mock.mock_open()
        mock_open.return_value.__enter__.return_value.read.return_value = b"FILE-CONTENTS"

        mock_stat = mock.Mock()
        mock_stat.return_value.st_size = 13
        mock_stat.return_value.st_mtime = 305419896.567

        original_path = pathlib.Path("./PATH/TO/FILENAME")
        path = mock.MagicMock(spec=pathlib.Path, stat=mock_stat, parts=original_path.parts)

        self.pbo_writer.add_file(path)

        with mock.patch("builtins.open", mock_open):
            self.pbo_writer.write(output)

        mock_stat.assert_called_once_with()

        mock_open.assert_called_once_with(path, "rb")

        assert b"PATH\\TO\\FILENAME\x00\x00\x00\x00\x00\x0d\x00\x00\x00\x00\x00\x00\x00" \
            b"\x78\x56\x34\x12\x0d\x00\x00\x00" + (b"\x00" * 21) + b"FILE-CONTENTS" \
            == output.getvalue()[22:]
