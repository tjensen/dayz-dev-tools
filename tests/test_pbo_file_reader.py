import io
import unittest
from unittest import mock

from dayz_dev_tools import pbo_file_reader


class TestPBOFileReader(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.content_file = io.BytesIO(b"0123456789abcdefXXX")
        self.reader = pbo_file_reader.PBOFileReader(self.content_file, 5, 11)

    def test_insufficient_bytes_exception_has_descriptive_message(self) -> None:
        with self.assertRaises(Exception) as error:
            raise pbo_file_reader.InsufficientBytes()

        assert str(error.exception) \
            == "Not enough bytes remaining for read; perhaps this is not a valid PBO file?"

    def test_read_returns_bytes_read_from_the_content_offset(self) -> None:
        result = self.reader.read(10)

        assert result == b"56789abcde"

    def test_read_returns_bytes_following_previous_read(self) -> None:
        self.reader.read(3)

        result = self.reader.read(5)

        assert result == b"89abc"

    def test_read_returns_bytes_up_to_end_of_content_when_size_exceeds_remaining_content(
        self
    ) -> None:
        result = self.reader.read(99)

        assert result == b"56789abcdef"

    def test_readz_returns_bytes_leading_up_to_the_first_zero_byte(self) -> None:
        self.content_file.getbuffer()[10] = 0

        result = self.reader.readz()

        assert result == b"56789"

    def test_readz_returns_bytes_to_end_of_content_if_no_zero_byte_is_found(self) -> None:
        result = self.reader.readz()

        assert result == b"56789abcdef"

    def test_readz_returns_bytes_following_previous_readz(self) -> None:
        self.content_file.getbuffer()[10] = 0
        self.reader.readz()

        result = self.reader.readz()

        assert result == b"bcdef"

    def test_readz_returns_bytes_following_previous_read(self) -> None:
        self.content_file.getbuffer()[10] = 0
        self.reader.read(2)

        result = self.reader.readz()

        assert result == b"789"

    def test_read_returns_bytes_following_previous_readz(self) -> None:
        self.content_file.getbuffer()[10] = 0
        self.reader.readz()

        result = self.reader.read(4)

        assert result == b"bcde"

    def test_readuint_returns_four_bytes_as_unsigned_integer(self) -> None:
        self.content_file.getbuffer()[5] = 0x50
        self.content_file.getbuffer()[6] = 0x60
        self.content_file.getbuffer()[7] = 0x70
        self.content_file.getbuffer()[8] = 0x80
        result = self.reader.readuint()

        assert result == 0x80706050

    def test_readuint_raises_when_four_bytes_are_not_available(self) -> None:
        self.reader.seek(10)

        with self.assertRaises(pbo_file_reader.InsufficientBytes):
            self.reader.readuint()

    def test_readuword_returns_two_bytes_as_unsigned_word(self) -> None:
        self.content_file.getbuffer()[5] = 0x55
        self.content_file.getbuffer()[6] = 0x66
        result = self.reader.readuword()

        assert result == 0x6655

    def test_readuword_raises_when_four_bytes_are_not_available(self) -> None:
        self.reader.seek(10)

        with self.assertRaises(pbo_file_reader.InsufficientBytes):
            self.reader.readuword()

    def test_tell_returns_current_position_in_content(self) -> None:
        assert self.reader.tell() == 0

        self.reader.read(5)

        assert self.reader.tell() == 5

    def test_seek_changes_current_position_in_content(self) -> None:
        self.reader.seek(5)

        assert self.reader.tell() == 5

    def test_seek_does_not_allow_setting_position_past_end_of_content(self) -> None:
        self.reader.seek(30)

        assert self.reader.tell() == 11

    def test_eof_returns_false_if_current_position_is_not_at_the_end_of_content(self) -> None:
        assert self.reader.eof() is False

    def test_eof_returns_true_if_current_position_is_at_the_end_of_content(self) -> None:
        self.reader.seek(11)

        assert self.reader.eof() is True

    def test_subreader_returns_pbo_file_reader_for_part_of_file(self) -> None:
        with mock.patch("dayz_dev_tools.pbo_file_reader.PBOFileReader") \
                as mock_pbo_file_reader_class:
            subreader = self.reader.subreader(3, 5)

        assert subreader == mock_pbo_file_reader_class.return_value

        mock_pbo_file_reader_class.assert_called_once_with(self.content_file, 8, 5)

    def test_subreader_cannot_read_beyond_end_of_content(self) -> None:
        with mock.patch("dayz_dev_tools.pbo_file_reader.PBOFileReader") \
                as mock_pbo_file_reader_class:
            subreader = self.reader.subreader(3, 10)

        assert subreader == mock_pbo_file_reader_class.return_value

        mock_pbo_file_reader_class.assert_called_once_with(self.content_file, 8, 8)
