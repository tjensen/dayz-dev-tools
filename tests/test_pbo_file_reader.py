import io
import unittest

from dayz import pbo_file_reader


class TestPBOFileReader(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.content_file = io.BytesIO(b"0123456789abcdefXXX")
        self.reader = pbo_file_reader.PBOFileReader(self.content_file, 5, 11)

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
