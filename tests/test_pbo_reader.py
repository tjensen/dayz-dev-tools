import io
import os
import unittest

from dayz_dev_tools import pbo_reader


class TestPBOReader(unittest.TestCase):
    def test_files_returns_empty_list_when_pbo_is_empty(self) -> None:
        reader = pbo_reader.PBOReader(io.BytesIO(b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"))

        assert reader.files() == []

    def test_files_returns_empty_list_when_pbo_has_empty_file_list(self) -> None:
        reader = pbo_reader.PBOReader(io.BytesIO())

        assert reader.files() == []

    def test_files_returns_list_of_files_in_pbo(self) -> None:
        pbo_file = io.BytesIO(
            b"f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"f2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        files = reader.files()

        assert len(files) == 2

        assert files[0].filename == b"f1"
        assert files[0].mime_type == b"\x01\x02\x03\x04"
        assert files[0].original_size == 0x8070605
        assert files[0].reserved == 0xc0b0a09
        assert files[0].time_stamp == 0x100f0e0d
        assert files[0].data_size == 12
        assert files[0].content_reader is not None

        assert files[1].filename == b"f2"
        assert files[1].mime_type == b"\x11\x12\x13\x14"
        assert files[1].original_size == 0x18171615
        assert files[1].reserved == 0x1c1b1a19
        assert files[1].time_stamp == 0x201f1e1d
        assert files[1].data_size == 9
        assert files[1].content_reader is not None

        # Asserting out of order to ensure that subreader is created correctly
        assert files[1].content_reader.read(9) == b"file2data"
        assert files[0].content_reader.read(12) == b"file1content"

    def test_files_returns_list_of_files_when_pbo_has_headers(self) -> None:
        pbo_file = io.BytesIO(
            b"\0\x73\x72\x65\x56\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"foo\0bar\0"
            b"fizz\0buzz\0"
            b"\0"
            b"f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"f2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        files = reader.files()

        assert len(files) == 2

    def test_files_returns_list_of_files_when_pbo_has_headers_but_no_dummy_record(self) -> None:
        pbo_file = io.BytesIO(
            b"\0"
            b"foo\0bar\0"
            b"fizz\0buzz\0"
            b"\0"
            b"f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"f2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        files = reader.files()

        assert len(files) == 2

    def test_inserts_prefix_into_filenames_when_prefix_header_is_set(self) -> None:
        pbo_file = io.BytesIO(
            b"\0\x73\x72\x65\x56\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"prefix\0PREFIX\0"
            b"\0"
            b"f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"f2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        filenames = [f.filename for f in reader.files()]

        assert filenames == [b"PREFIX\\f1", b"PREFIX\\f2"]

    def test_file_returns_none_if_filename_string_does_not_match_any_in_pbo(self) -> None:
        pbo_file = io.BytesIO(
            b"dir\\f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"dir\\f2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        matching_file = reader.file("unmatched")

        assert matching_file is None

    def test_file_returns_none_if_filename_bytes_does_not_match_any_in_pbo(self) -> None:
        pbo_file = io.BytesIO(
            b"dir\\f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"dir\\f2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        matching_file = reader.file(b"unmatched")

        assert matching_file is None

    def test_file_returns_file_with_matching_filename_string(self) -> None:
        pbo_file = io.BytesIO(
            b"dir\\f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"dir\\f2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        matching_file = reader.file(os.path.join("dir", "f1"))

        assert matching_file == reader.files()[0]

    def test_file_matches_string_names_case_insensitively(self) -> None:
        pbo_file = io.BytesIO(
            b"dir\\f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"Dir\\F2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        matching_file = reader.file(os.path.join("dir", "F2"))

        assert matching_file == reader.files()[1]

    def test_file_returns_file_with_matching_filename_bytes(self) -> None:
        pbo_file = io.BytesIO(
            b"dir\\f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"dir\\f2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        matching_file = reader.file(b"dir\\f1")

        assert matching_file == reader.files()[0]

    def test_file_matches_bytes_names_case_insensitively(self) -> None:
        pbo_file = io.BytesIO(
            b"dir\\f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"Dir\\F2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        matching_file = reader.file(b"dir\\f2")

        assert matching_file == reader.files()[1]

    def test_headers_returns_empty_list_when_pbo_is_empty(self) -> None:
        reader = pbo_reader.PBOReader(io.BytesIO())

        assert reader.headers() == []

    def test_headers_returns_empty_list_when_pbo_does_not_have_headers(self) -> None:
        pbo_file = io.BytesIO(
            b"f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"f2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        assert reader.headers() == []

    def test_headers_returns_list_of_headers_when_pbo_has_headers(self) -> None:
        pbo_file = io.BytesIO(
            b"\0\x73\x72\x65\x56\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"foo\0bar\0"
            b"fizz\0buzz\0"
            b"foo\0repeated keys are not ignored or overwritten\0"
            b"\0"
            b"f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"f2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        headers = reader.headers()

        assert headers == [
            (b"foo", b"bar"),
            (b"fizz", b"buzz"),
            (b"foo", b"repeated keys are not ignored or overwritten")
        ]

    def test_headers_returns_list_of_headers_when_pbo_has_headers_but_no_dummy_record(self) -> None:
        pbo_file = io.BytesIO(
            b"\0"
            b"foo\0bar\0"
            b"fizz\0buzz\0"
            b"\0"
            b"f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"f2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        headers = reader.headers()

        assert headers == [
            (b"foo", b"bar"),
            (b"fizz", b"buzz")
        ]

    def test_prefix_returns_none_if_prefix_header_is_not_present(self) -> None:
        pbo_file = io.BytesIO(
            b"\0"
            b"foo\0bar\0"
            b"fizz\0buzz\0"
            b"\0"
            b"f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"f2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        assert reader.prefix() is None

    def test_prefix_returns_prefix_header_value_when_present(self) -> None:
        pbo_file = io.BytesIO(
            b"\0"
            b"foo\0bar\0"
            b"prefix\0PREFIX\0"
            b"fizz\0buzz\0"
            b"\0"
            b"f1\0\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x0c\0\0\0"
            b"f2\0\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x09\0\0\0"
            b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
            b"file1content"
            b"file2data")
        reader = pbo_reader.PBOReader(pbo_file)

        assert reader.prefix() == b"PREFIX"
