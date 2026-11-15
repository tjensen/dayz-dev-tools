import unittest

from dayz_dev_tools_rust import compute_checksum, expand


class TestExpand(unittest.TestCase):
    def test_expands_previously_compressed_data(self) -> None:
        assert expand(b"\xffABCDEFGH\0\x07\x01", 12) == b"ABCDEFGHBCDE"

    def test_expands_data_from_bytearray(self) -> None:
        assert expand(bytearray(b"\xffABCDEFGH\0\x07\x01"), 12) == b"ABCDEFGHBCDE"

    def test_expand_does_not_overflow_capacity_on_overlapping_repeat(self) -> None:
        # b"\x0fABCD\x02\x07" expands to 14 bytes (ABCDCDCDCDCDCD) if unbounded,
        # but capacity is 7. Output must be exactly 7 bytes.
        result = expand(b"\x0fABCD\x02\x07", 7)
        assert result == b"ABCDCDC"
        assert len(result) == 7

    def test_expand_terminates_safely_when_pointer_has_zero_offset(self) -> None:
        # A zero pointer offset must not cause an infinite loop.
        assert expand(b"\x00\x00\x00", 10) == b""

    def test_compute_checksum_returns_sum_of_bytes(self) -> None:
        assert compute_checksum(b"ABCDEFGH") == 0x224
        assert compute_checksum(b"") == 0

    def test_compute_checksum_accepts_bytearray(self) -> None:
        assert compute_checksum(bytearray(b"ABCDEFGH")) == 0x224

    def test_compute_checksum_wraps_at_32_bits(self) -> None:
        # Sum of 20,000,000 bytes with value 255 is 5,100,000,000 > 2^32 - 1 (4,294,967,295)
        # 5,100,000,000 % 2^32 = 805,032,704 (0x2ffcfb00)
        chunk = b"\xff" * 100_000
        # 43 iterations of 100,000 bytes = 4,300,000 bytes * 255 = 1,096,500,000
        # Let's verify with 17,000,000 bytes: 17,000,000 * 255 = 4,335,000,000 = 0x102636b00
        # Expected u32 wrapped: 0x02636b00 = 40,069,888
        data = b"\xff" * 17_000_000
        assert compute_checksum(data) == 40_032_704

    def test_expand_raises_type_error_for_invalid_input_type(self) -> None:
        with self.assertRaises(TypeError):
            expand("not bytes", 10)  # type: ignore[arg-type]
