import io
import unittest

from dayz_dev_tools import expand
from dayz_dev_tools import pbo_file_reader


class TestExpand(unittest.TestCase):
    def test_expands_previously_compressed_data(self) -> None:
        inbytes = b"\xffABCDEFGH\0\x07\x01"
        infile = pbo_file_reader.PBOFileReader(io.BytesIO(inbytes), 0, len(inbytes))

        outbytes = expand.expand(infile, 12)

        assert outbytes == b"ABCDEFGHBCDE"
