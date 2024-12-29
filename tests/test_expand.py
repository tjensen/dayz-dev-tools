import unittest

from dayz_dev_tools_rust import expand


class TestExpand(unittest.TestCase):
    def test_expands_previously_compressed_data(self) -> None:
        assert expand(b"\xffABCDEFGH\0\x07\x01", 12) == b"ABCDEFGHBCDE"
