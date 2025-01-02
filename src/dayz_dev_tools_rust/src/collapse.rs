use memchr::memmem;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::{pyfunction, PyResult, Python};
use pyo3::types::{PyBytes, PyBytesMethods};
use pyo3::Bound;
use std::cmp;

type Result<T> = std::result::Result<T, CollapseError>;

#[derive(Debug, Clone)]
struct CollapseError;

struct FlagBits {
    bits: u8,
    size: u8,
}

impl FlagBits {
    fn new() -> FlagBits {
        FlagBits { bits: 0, size: 0 }
    }

    fn empty(&self) -> bool {
        self.size == 0
    }

    fn full(&self) -> bool {
        self.size == 8
    }

    fn push(&mut self, value: bool) {
        if self.full() {
            panic!("FlagBits is full!");
        }

        if value {
            self.bits |= 1 << self.size;
        }
        self.size += 1;
    }

    fn value(&self) -> u8 {
        self.bits
    }
}

struct Packet {
    flagbits: FlagBits,
    chunk: Vec<u8>,
}

impl Packet {
    fn new() -> Packet {
        Packet {
            flagbits: FlagBits::new(),
            chunk: Vec::with_capacity(16),
        }
    }

    fn empty(&self) -> bool {
        self.flagbits.empty()
    }

    fn full(&self) -> bool {
        self.flagbits.full()
    }

    fn push_byte(&mut self, value: u8) {
        self.flagbits.push(true);
        self.chunk.push(value);
    }

    fn push_pointer(&mut self, rpos: u16, rlen: u16) {
        self.flagbits.push(false);
        let ptr = (rpos & 0xf00) << 4 | (rpos & 0xff) | (((rlen - 3) & 0xf) << 8);
        self.chunk.extend(ptr.to_le_bytes());
    }

    fn value(&self) -> Vec<u8> {
        let mut result = Vec::with_capacity(self.chunk.len() + 1);
        result.push(self.flagbits.value());
        result.extend(&self.chunk);
        result
    }

    fn size(&self) -> usize {
        self.chunk.len() + 1
    }
}

fn collapse_impl(input: &[u8]) -> Result<Vec<u8>> {
    let mut output = Vec::<u8>::with_capacity(input.len());
    let max_outbytes = input.len() - 4; // reserve room for checksum
    let mut packet = Packet::new();
    let mut offset = 0;

    'outer: while offset < input.len() {
        if packet.full() {
            if output.len() + packet.size() > max_outbytes {
                return Err(CollapseError);
            }

            output.extend(&packet.value());
            packet = Packet::new();
        }

        for needle_len in
            std::ops::RangeInclusive::new(3, cmp::min(18, input.len() - offset)).rev()
        {
            let needle = &input[offset..offset + needle_len];
            let haystack = &input[offset - cmp::min(0x1000, offset)..offset];
            if let Some(index) = memmem::find(haystack, needle) {
                let pos = (offset - index) as u16;
                packet.push_pointer(pos, needle_len as u16);
                offset += needle_len;
                continue 'outer;
            }
        }

        packet.push_byte(input[offset]);
        offset += 1;
    }

    if !packet.empty() {
        if output.len() + packet.size() > max_outbytes {
            return Err(CollapseError);
        }

        output.extend(&packet.value());
    }

    output.extend(
        input
            .iter()
            .fold(0u32, |sum, b| sum + *b as u32)
            .to_le_bytes(),
    );

    Ok(output)
}

#[pyfunction]
pub fn collapse<'p>(py: Python<'p>, input: &'p Bound<'p, PyBytes>) -> PyResult<Bound<'p, PyBytes>> {
    match collapse_impl(input.as_bytes()) {
        Ok(output) => Ok(PyBytes::new(py, &output)),
        Err(_) => Err(PyValueError::new_err("input is not compressible")),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_flagbits_starts_empty() {
        let flagbits = FlagBits::new();

        assert!(flagbits.empty());
        assert!(!flagbits.full());
        assert_eq!(flagbits.value(), 0);
    }

    #[test]
    fn test_flagbits_becomes_not_empty_when_true_is_pushed() {
        let mut flagbits = FlagBits::new();

        flagbits.push(true);

        assert!(!flagbits.empty());
        assert!(!flagbits.full());
        assert_eq!(flagbits.value(), 1);
    }

    #[test]
    fn test_flagbits_becomes_not_empty_when_false_is_pushed() {
        let mut flagbits = FlagBits::new();

        flagbits.push(false);

        assert!(!flagbits.empty());
        assert!(!flagbits.full());
        assert_eq!(flagbits.value(), 0);
    }

    #[test]
    fn test_flagbits_pushes_bits_in_order() {
        let mut flagbits = FlagBits::new();

        flagbits.push(false);
        flagbits.push(true);
        flagbits.push(false);
        flagbits.push(true);
        flagbits.push(false);
        flagbits.push(true);

        assert!(!flagbits.empty());
        assert!(!flagbits.full());
        assert_eq!(flagbits.value(), 0x2a);
    }

    #[test]
    fn test_flagbits_becomes_full_when_eight_bits_are_pushed() {
        let mut flagbits = FlagBits::new();

        flagbits.push(false);
        flagbits.push(true);
        flagbits.push(false);
        flagbits.push(true);
        flagbits.push(false);
        flagbits.push(true);
        flagbits.push(false);
        flagbits.push(true);

        assert!(!flagbits.empty());
        assert!(flagbits.full());
        assert_eq!(flagbits.value(), 0xaa);
    }

    #[test]
    #[should_panic(expected = "FlagBits is full!")]
    fn test_flagbits_panics_when_pushing_more_than_eight_bits() {
        let mut flagbits = FlagBits::new();

        flagbits.push(false);
        flagbits.push(true);
        flagbits.push(false);
        flagbits.push(true);
        flagbits.push(false);
        flagbits.push(true);
        flagbits.push(false);
        flagbits.push(true);
        flagbits.push(false);
    }

    #[test]
    fn test_packet_starts_empty() {
        let packet = Packet::new();

        assert!(packet.empty());
        assert!(!packet.full());
        assert_eq!(packet.size(), 1);
        assert_eq!(packet.value(), b"\x00");
    }

    #[test]
    fn test_packet_becomes_not_empty_when_byte_is_pushed() {
        let mut packet = Packet::new();

        packet.push_byte(0x42);

        assert!(!packet.empty());
        assert!(!packet.full());
        assert_eq!(packet.size(), 2);
        assert_eq!(packet.value(), b"\x01\x42");
    }

    #[test]
    fn test_packet_becomes_not_empty_when_pointer_is_pushed() {
        let mut packet = Packet::new();

        packet.push_pointer(0x876, 4);

        assert!(!packet.empty());
        assert!(!packet.full());
        assert_eq!(packet.size(), 3);
        assert_eq!(packet.value(), b"\x00\x76\x81");
    }

    #[test]
    fn test_packet_pushes_in_order() {
        let mut packet = Packet::new();

        packet.push_byte(0x11);
        packet.push_pointer(0x876, 4);
        packet.push_byte(0x22);
        packet.push_pointer(0xfff, 3);
        packet.push_byte(0x33);
        packet.push_pointer(0x000, 18);

        assert!(!packet.empty());
        assert!(!packet.full());
        assert_eq!(packet.size(), 10);
        assert_eq!(packet.value(), b"\x15\x11\x76\x81\x22\xff\xf0\x33\x00\x0f");
    }

    #[test]
    fn test_packet_becomes_full_after_eight_pushes() {
        let mut packet = Packet::new();

        packet.push_byte(0x11);
        packet.push_pointer(0x876, 4);
        packet.push_byte(0x22);
        packet.push_pointer(0xfff, 3);
        packet.push_byte(0x33);
        packet.push_pointer(0x000, 18);
        packet.push_byte(0x44);
        packet.push_pointer(0x888, 11);

        assert!(!packet.empty());
        assert!(packet.full());
        assert_eq!(packet.size(), 13);
        assert_eq!(
            packet.value(),
            b"\x55\x11\x76\x81\x22\xff\xf0\x33\x00\x0f\x44\x88\x88"
        );
    }

    #[test]
    #[should_panic(expected = "FlagBits is full!")]
    fn test_packet_panics_when_pushing_more_than_eight_times() {
        let mut packet = Packet::new();

        packet.push_byte(0x11);
        packet.push_pointer(0x876, 4);
        packet.push_byte(0x22);
        packet.push_pointer(0xfff, 3);
        packet.push_byte(0x33);
        packet.push_pointer(0x000, 18);
        packet.push_byte(0x44);
        packet.push_pointer(0x888, 11);
        packet.push_byte(0x55);
    }

    #[test]
    fn test_collapse_returns_error_if_input_cannot_be_compressed() {
        assert!(collapse_impl(b"ABCDEFGH").is_err());
    }

    #[test]
    fn test_collapse_compresses_compressible_input() {
        let outbytes = collapse_impl(b"ABCDABCDABCDABCD").unwrap();

        assert_eq!(outbytes, b"\x0fABCD\x04\x01\x08\x05\x28\x04\x00\x00");
    }

    #[test]
    fn test_collapse_compresses_compressible_input_using_smallest_repeatable_chunk() {
        let outbytes = collapse_impl(b"ABCABCDEFGABCHIJABCDEFG").unwrap();

        assert_eq!(
            outbytes,
            b"\xf7ABC\x03\x00DEFG\x0e\x0a\x00HIJ\x0d\x04\x1f\x06\x00\x00"
        );
    }

    #[test]
    fn test_collapse_compresses_compressible_input_using_largest_repeatable_chunk() {
        let outbytes = collapse_impl(b"ABCDEFGHIJKLMNOPQRABCDEFGHIJKLMNOPQR").unwrap();

        assert_eq!(
            outbytes,
            b"\xffABCDEFGH\xffIJKLMNOP\x03QR\x12\x0f\x56\x0a\x00\x00"
        );
    }
}
