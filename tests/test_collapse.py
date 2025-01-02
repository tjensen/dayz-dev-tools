import pytest
import unittest

from dayz_dev_tools_rust import collapse


class TestCollapse(unittest.TestCase):
    def test_compresses_compressible_data(self) -> None:
        assert collapse(b"ABCDEFGHIJKLMNOPQRABCDEFGHIJKLMNOPQR") \
            == b"\xffABCDEFGH\xffIJKLMNOP\x03QR\x12\x0f\x56\x0a\x00\x00"

    def test_raises_when_data_cannot_be_compressed(self) -> None:
        with pytest.raises(ValueError, match=r"input is not compressible"):
            collapse(b"ABCDEFGH")
