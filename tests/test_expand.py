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
        assert 0x0262_d9c0 == compute_checksum(b"\xff" * 17_000_000)

    def test_expand_raises_type_error_for_invalid_input_type(self) -> None:
        with self.assertRaises(TypeError):
            expand("not bytes", 10)  # type: ignore[arg-type]
