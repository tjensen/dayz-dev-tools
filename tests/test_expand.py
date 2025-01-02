import pytest
import unittest

from dayz_dev_tools_rust import expand


class TestExpand(unittest.TestCase):
    def test_expands_previously_compressed_data(self) -> None:
        assert expand(b"\xffABCDEFGH\0\x07\x01\x32\x03\x00\x00", 12) == b"ABCDEFGHBCDE"

    def test_raises_when_expanded_data_does_not_match_checksum(self) -> None:
        with pytest.raises(ValueError, match=r"^Checksum mismatch \(0x332 != 0xffffffff\)$"):
            expand(b"\xffABCDEFGH\0\x07\x01\xff\xff\xff\xff", 12)
