import io
import os
import unittest
from unittest import mock

from dayz import pbo_file
from dayz import pbo_file_reader


class TestPBOFile(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mock_content_reader = mock.Mock(spec=pbo_file_reader.PBOFileReader)
        self.pbofile = pbo_file.PBOFile(b"FILENAME", b"ABCD", 12345, 0x11223344, 0x44332211, 4321)

    def test_instance_has_given_attributes(self) -> None:
        assert self.pbofile.filename == b"FILENAME"
        assert self.pbofile.mime_type == b"ABCD"
        assert self.pbofile.original_size == 12345
        assert self.pbofile.reserved == 0x11223344
        assert self.pbofile.time_stamp == 0x44332211
        assert self.pbofile.data_size == 4321
        assert self.pbofile.content_reader is None

    def test_unpack_writes_uncompressed_contents_to_output_file_when_original_size_is_0(
        self
    ) -> None:
        self.pbofile.content_reader = self.mock_content_reader
        self.pbofile.original_size = 0
        self.mock_content_reader.read.return_value = b"ABCD1234"
        output = io.BytesIO()

        self.pbofile.unpack(output)

        assert output.getvalue() == b"ABCD1234"

        self.mock_content_reader.read.assert_called_once_with(4321)

    def test_unpack_writes_uncompressed_contents_to_output_file_when_original_size_is_data_size(
        self
    ) -> None:
        self.pbofile.content_reader = self.mock_content_reader
        self.pbofile.original_size = 4321
        self.mock_content_reader.read.return_value = b"ABCD1234"
        output = io.BytesIO()

        self.pbofile.unpack(output)

        assert output.getvalue() == b"ABCD1234"

        self.mock_content_reader.read.assert_called_once_with(4321)

    def test_normalized_filename_returns_filenames_with_os_style_paths(self) -> None:
        self.pbofile.filename = b"xxx\\yyy\\zzz.www"

        assert self.pbofile.normalized_filename() == os.path.join(b"xxx", b"yyy", b"zzz.www")

    def test_split_filename_returns_filename_split_on_path_separators(self) -> None:
        self.pbofile.filename = b"xxx\\yyy\\zzz.www"

        assert self.pbofile.split_filename() == [b"xxx", b"yyy", b"zzz.www"]
