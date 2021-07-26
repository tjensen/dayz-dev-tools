import io
import unittest

from dayz_dev_tools import expand
from dayz_dev_tools import pbo_file_reader


class TestExpand(unittest.TestCase):
    def test_expands_trivially_compressed_file(self) -> None:
        inbytes = b"\xffABCDEFGH\xffIJKLMNOP\xffQRSTUVWX"
        infile = pbo_file_reader.PBOFileReader(io.BytesIO(inbytes), 0, len(inbytes))

        outbytes = expand.expand(infile)

        assert outbytes == b"ABCDEFGHIJKLMNOPQRSTUVWX"

    def test_stops_extracting_bytes_when_end_of_content_is_reached_within_packet(self) -> None:
        inbytes = b"\xffABCDE"
        infile = pbo_file_reader.PBOFileReader(io.BytesIO(inbytes), 0, len(inbytes))

        outbytes = expand.expand(infile)

        assert outbytes == b"ABCDE"

    def test_expands_previously_compressed_data(self) -> None:
        inbytes = b"\xffABCDEFGH\0\x07\x01"
        infile = pbo_file_reader.PBOFileReader(io.BytesIO(inbytes), 0, len(inbytes))

        outbytes = expand.expand(infile)

        assert outbytes == b"ABCDEFGHBCDE"

    def test_inserts_spaces_when_compressed_data_references_negative_offset(self) -> None:
        inbytes = b"\x0fABCD\x05\x0f"
        infile = pbo_file_reader.PBOFileReader(io.BytesIO(inbytes), 0, len(inbytes))

        outbytes = expand.expand(infile)

        assert outbytes == b"ABCD                  "

    def test_repeats_previous_data_when_length_extends_beyond_end_of_data(self) -> None:
        inbytes = b"\x0fABCD\x02\x07"
        infile = pbo_file_reader.PBOFileReader(io.BytesIO(inbytes), 0, len(inbytes))

        outbytes = expand.expand(infile)

        assert outbytes == b"ABCDCDCDCDCDCD"

    def test_does_not_repeat_to_insert_more_than_requested_number_of_characters(self) -> None:
        inbytes = b"\x0fABCD\x02\x08"
        infile = pbo_file_reader.PBOFileReader(io.BytesIO(inbytes), 0, len(inbytes))

        outbytes = expand.expand(infile)

        assert outbytes == b"ABCDCDCDCDCDCDC"
