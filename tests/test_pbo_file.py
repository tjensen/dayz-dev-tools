import io
import os
import unittest
from unittest import mock

from dayz_dev_tools import pbo_file
from dayz_dev_tools import pbo_file_reader


class TestNormalizeFilename(unittest.TestCase):
    def test_returns_filenames_with_os_style_paths(self) -> None:
        filename = [b"xxx", b"yyy", b"zzz.www"]

        assert pbo_file.normalize_filename(filename) == os.path.join("xxx", "yyy", "zzz.www")

    def test_replaces_invalid_characters(self) -> None:
        filename = [b"x\x88x", b"y\x99y", b"z\xaaz.www"]

        assert pbo_file.normalize_filename(filename) == \
            os.path.join("x\ufffdx", "y\ufffdy", "z\ufffdz.www")


class TestPBOFile(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mock_content_reader = mock.Mock(spec=pbo_file_reader.PBOFileReader)
        self.pbofile = pbo_file.PBOFile(
            b"PREFIX", b"FILENAME", b"ABCD", 12345, 0x11223344, 0x44332211, 4321)

    def test_instance_has_given_attributes(self) -> None:
        assert self.pbofile.prefix == b"PREFIX"
        assert self.pbofile.filename == b"FILENAME"
        assert self.pbofile.mime_type == b"ABCD"
        assert self.pbofile.original_size == 12345
        assert self.pbofile.reserved == 0x11223344
        assert self.pbofile.time_stamp == 0x44332211
        assert self.pbofile.data_size == 4321
        assert self.pbofile.content_reader is None

    def test_prefix_is_optional(self) -> None:
        pbofile = pbo_file.PBOFile(None, b"FILENAME", b"ABCD", 12345, 0x11223344, 0x44332211, 4321)

        assert pbofile.prefix is None

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

    def test_unpack_writes_expanded_content_to_output_file_when_compressed(self) -> None:
        self.pbofile.original_size = 8
        self.pbofile.data_size = 13
        self.pbofile.content_reader = pbo_file_reader.PBOFileReader(
            io.BytesIO(b"\xffABCDEFGH\x24\x02\0\0"), 0, 13)
        output = io.BytesIO()

        self.pbofile.unpack(output)

        assert output.getvalue() == b"ABCDEFGH"

    def test_unpack_raises_if_checksum_of_expanded_content_does_not_match(self) -> None:
        self.pbofile.original_size = 8
        self.pbofile.data_size = 13
        self.pbofile.content_reader = pbo_file_reader.PBOFileReader(
            io.BytesIO(b"\xffABCDEFGH\x23\x02\0\0"), 0, 13)
        output = io.BytesIO()

        with self.assertRaises(Exception) as error:
            self.pbofile.unpack(output)

        assert str(error.exception) == "Checksum mismatch (0x224 != 0x223)"

        assert len(output.getvalue()) == 0

    def test_normalized_filename_returns_filenames_with_os_style_paths(self) -> None:
        self.pbofile.filename = b"xxx\\yyy\\zzz.www"

        assert self.pbofile.normalized_filename() == os.path.join("PREFIX", "xxx", "yyy", "zzz.www")

    def test_normalized_filename_does_not_include_prefix_when_none(self) -> None:
        self.pbofile.prefix = None
        self.pbofile.filename = b"xxx\\yyy\\zzz.www"

        assert self.pbofile.normalized_filename() == os.path.join("xxx", "yyy", "zzz.www")

    def test_normalized_filename_replaces_invalid_characters(self) -> None:
        self.pbofile.prefix = b"a\x88b"
        self.pbofile.filename = b"x\x88x\\y\x99y\\z\xaaz.www"

        assert self.pbofile.normalized_filename() == \
            os.path.join("a\ufffdb", "x\ufffdx", "y\ufffdy", "z\ufffdz.www")

    def test_split_filename_returns_filename_split_on_path_separators(self) -> None:
        self.pbofile.filename = b"xxx\\yyy\\zzz.www"

        assert self.pbofile.split_filename() == [b"PREFIX", b"xxx", b"yyy", b"zzz.www"]

    def test_split_filename_does_not_include_prefix_when_none(self) -> None:
        self.pbofile.prefix = None
        self.pbofile.filename = b"xxx\\yyy\\zzz.www"

        assert self.pbofile.split_filename() == [b"xxx", b"yyy", b"zzz.www"]

    def test_split_filename_handles_mixed_path_separators(self) -> None:
        self.pbofile.filename = b"\\xxx/yyy\\/zzz.www"

        assert self.pbofile.split_filename() == [b"PREFIX", b"xxx", b"yyy", b"zzz.www"]

    def test_split_filename_handles_bogus_obfuscation_filename(self) -> None:
        self.pbofile.prefix = None
        self.pbofile.filename = b"\\\\\\"

        assert self.pbofile.split_filename() == [b""]

    def test_unpacked_size_returns_original_size(self) -> None:
        assert self.pbofile.unpacked_size() == 12345

    def test_unpacked_size_returns_data_size_if_original_size_is_zero(self) -> None:
        self.pbofile.original_size = 0

        assert self.pbofile.unpacked_size() == 4321

    def test_type_returns_mime_type_as_displayable_string(self) -> None:
        assert self.pbofile.type() == "ABCD"

    def test_type_pads_string_to_be_four_characters(self) -> None:
        self.pbofile.mime_type = b"A"

        assert self.pbofile.type() == "A   "

    def test_type_replaces_non_ascii_characters(self) -> None:
        self.pbofile.mime_type = b"A\x88\x99D"

        assert self.pbofile.type() == "A  D"

    def test_type_replaces_control_characters(self) -> None:
        self.pbofile.mime_type = b"A\x01\x7fD"

        assert self.pbofile.type() == "A  D"

    def test_invalid_returns_false_when_filename_is_valid(self) -> None:
        assert self.pbofile.invalid() is False

    def test_invalid_returns_true_when_filename_contains_asterisk(self) -> None:
        self.pbofile.filename = b"FILE*NAME"

        assert self.pbofile.invalid() is True

    def test_invalid_returns_true_when_filename_contains_question_mark(self) -> None:
        self.pbofile.filename = b"FILE?NAME"

        assert self.pbofile.invalid() is True

    def test_invalid_returns_true_when_filename_contains_pipe(self) -> None:
        self.pbofile.filename = b"FILE|NAME"

        assert self.pbofile.invalid() is True

    def test_invalid_returns_true_when_filename_contains_double_quote(self) -> None:
        self.pbofile.filename = b"FILE\"NAME"

        assert self.pbofile.invalid() is True

    def test_invalid_returns_true_when_filename_contains_colon(self) -> None:
        self.pbofile.filename = b"FILE:NAME"

        assert self.pbofile.invalid() is True

    def test_invalid_returns_true_when_filename_contains_greater_than(self) -> None:
        self.pbofile.filename = b"FILE>NAME"

        assert self.pbofile.invalid() is True

    def test_invalid_returns_true_when_filename_contains_less_than(self) -> None:
        self.pbofile.filename = b"FILE<NAME"

        assert self.pbofile.invalid() is True

    def test_invalid_returns_true_when_filename_contains_tab(self) -> None:
        self.pbofile.filename = b"FILE\tNAME"

        assert self.pbofile.invalid() is True

    def test_invalid_returns_true_when_filename_contains_extended_characters(self) -> None:
        self.pbofile.filename = b"FILE\x88NAME"

        assert self.pbofile.invalid() is True

    def test_invalid_returns_true_when_filename_contains_reserved_names(self) -> None:
        bad_names = [
            b"dir\\CON",
            b"dir\\PRN.ext",
            b"dir\\AUX\\def",
            b"dir\\NUL.ext\\ghi",
            b"dir\\COM5.whatever\\jkl",
            b"dir\\LPT8.blargh\\mno"
        ]

        for name in bad_names:
            self.pbofile.filename = name

            assert self.pbofile.invalid() is True

    def test_obfuscated_returns_false_when_filename_is_valid(self) -> None:
        assert self.pbofile.obfuscated() is False

    def test_obfuscated_returns_true_when_filename_is_invalid_and_has_c_extension(self) -> None:
        self.pbofile.filename = b"FILE\x88NAME.c"

        assert self.pbofile.obfuscated() is True

    def test_obfuscated_returns_false_when_filename_does_not_have_c_extension(self) -> None:
        self.pbofile.filename = b"FILE\x88NAME"

        assert self.pbofile.obfuscated() is False

    def test_deobfuscated_filename_returns_normalized_filename_when_not_obfuscated(self) -> None:
        assert self.pbofile.deobfuscated_filename(42) == self.pbofile.normalized_filename()

    def test_deobfuscated_filename_returns_deobfuscated_filename_when_obfuscated(self) -> None:
        self.pbofile.filename = b"dir\\NUL.ext\\ghi.c"

        assert self.pbofile.deobfuscated_filename(42) == os.path.join(
            "PREFIX", "dir", "deobfs00042.c")

    def test_deobfuscated_split_returns_deobfuscated_filename_split_on_path_separators(
        self
    ) -> None:
        self.pbofile.filename = b"dir\\subdir\\bad\x88name\\whatever.c"

        assert self.pbofile.deobfuscated_split(42) == [
            b"PREFIX", b"dir", b"subdir", b"deobfs00042.c"
        ]

    def test_deobfuscated_split_removes_trailing_spaces_from_path_segments(self) -> None:
        self.pbofile.filename = b"dir\\subdir \\whatever.c"

        assert self.pbofile.deobfuscated_split(42) == [
            b"PREFIX", b"dir", b"subdir", b"whatever.c"
        ]
