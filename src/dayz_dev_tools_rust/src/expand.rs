use pyo3::prelude::{pyfunction, PyResult, Python};
use pyo3::types::{PyByteArray, PyByteArrayMethods, PyBytes, PyBytesMethods};
use pyo3::Bound;
use std::cmp::min;
use std::iter;

fn extract_bytes<'a>(obj: &'a Bound<'a, pyo3::PyAny>) -> PyResult<&'a [u8]> {
    if let Ok(b) = obj.cast::<PyBytes>() {
        Ok(b.as_bytes())
    } else if let Ok(ba) = obj.cast::<PyByteArray>() {
        Ok(unsafe { ba.as_bytes() })
    } else {
        Err(pyo3::exceptions::PyTypeError::new_err(
            "Expected bytes or bytearray",
        ))
    }
}

struct FlagBits {
    flags: u8,
    remaining: u8,
}

impl FlagBits {
    fn new(flags: u8) -> FlagBits {
        FlagBits {
            flags,
            remaining: 8,
        }
    }

    fn end(&self) -> bool {
        self.remaining == 0
    }

    fn pop(&mut self) -> bool {
        let result = self.flags & 1;
        self.flags >>= 1;
        self.remaining -= 1;
        result == 1
    }
}

struct InBuffer<'a> {
    raw: &'a [u8],
    i: usize,
}

impl<'a> InBuffer<'a> {
    fn new(raw: &'a [u8]) -> InBuffer<'a> {
        InBuffer { raw, i: 0 }
    }

    fn end(&self) -> bool {
        self.i >= self.raw.len()
    }

    fn readbyte(&mut self) -> Result<u8, &'static str> {
        if self.i >= self.raw.len() {
            return Err("end of input reached");
        }
        let result = self.raw[self.i];
        self.i += 1;
        Ok(result)
    }

    fn readword(&mut self) -> Result<u16, &'static str> {
        if self.i + 1 >= self.raw.len() {
            return Err("end of input reached");
        }
        let result = u16::from_le_bytes([self.raw[self.i], self.raw[self.i + 1]]);
        self.i += 2;
        Ok(result)
    }
}

pub fn compute_checksum(data: &[u8]) -> u32 {
    data.iter().fold(0u32, |acc, &b| acc.wrapping_add(b as u32))
}

fn expand_impl(inbytes: &[u8], capacity: usize) -> Vec<u8> {
    let mut raw = InBuffer::new(inbytes);
    let mut output = Vec::with_capacity(capacity);
    'outer: while !raw.end() && output.len() < capacity {
        if let Ok(flagbyte) = raw.readbyte() {
            let mut flagbits = FlagBits::new(flagbyte);
            while !flagbits.end() && output.len() < capacity {
                if flagbits.pop() {
                    if let Ok(b) = raw.readbyte() {
                        output.push(b);
                    } else {
                        break 'outer;
                    }
                } else if let Ok(ptr) = raw.readword() {
                    let rposi = ((ptr & 0xff) | ((ptr >> 4) & 0xf00)) as usize;
                    let rlen = (((ptr >> 8) & 0xf) + 3) as usize;

                    if rposi == 0 {
                        // Offset of 0 is invalid in LZSS back-referencing and would cause an infinite loop
                        break 'outer;
                    }

                    let count = min(rlen, capacity - output.len());

                    if rposi <= output.len() {
                        let rpos = output.len() - rposi;

                        if rpos + count <= output.len() {
                            output.extend_from_within(rpos..rpos + count);
                        } else {
                            let target_len = output.len() + count;
                            while output.len() < target_len {
                                let chunk = min(output.len() - rpos, target_len - output.len());
                                output.extend_from_within(rpos..rpos + chunk);
                            }
                        }
                    } else {
                        output.extend(iter::repeat_n(32u8, count));
                    }
                } else {
                    break 'outer;
                }
            }
        } else {
            break 'outer;
        }
    }
    output
}

#[pyfunction]
#[pyo3(name = "compute_checksum")]
pub fn py_compute_checksum(input: &Bound<'_, pyo3::PyAny>) -> PyResult<u32> {
    let bytes = extract_bytes(input)?;
    Ok(compute_checksum(bytes))
}

#[pyfunction]
pub fn expand<'p>(
    py: Python<'p>,
    input: &Bound<'p, pyo3::PyAny>,
    capacity: usize,
) -> PyResult<Bound<'p, PyBytes>> {
    let bytes = extract_bytes(input)?;
    let output = py.detach(|| expand_impl(bytes, capacity));

    Ok(PyBytes::new(py, &output))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_expand_expands_trivially_compressed_file() {
        let outbytes = expand_impl(b"\xffABCDEFGH\xffIJKLMNOP\xffQRSTUVWX", 24);

        assert_eq!(outbytes, b"ABCDEFGHIJKLMNOPQRSTUVWX");
    }

    #[test]
    fn test_expand_stops_extracting_bytes_when_end_of_content_is_reached_within_packet() {
        assert_eq!(expand_impl(b"\xffABCDE", 5), b"ABCDE");
    }

    #[test]
    fn test_expand_stops_extracting_bytes_when_end_of_output_buffer_is_reached() {
        assert_eq!(
            expand_impl(b"\xffABCDEFGH\xffIJKLMNOP\xffQRSTUVWX", 5),
            b"ABCDE"
        );
    }

    #[test]
    fn test_expand_expands_previously_compressed_data() {
        assert_eq!(expand_impl(b"\xffABCDEFGH\0\x07\x01", 12), b"ABCDEFGHBCDE");
    }

    #[test]
    fn test_expand_repeats_characters_from_beginning_of_output() {
        assert_eq!(expand_impl(b"\xffABCDEFGH\0\x08\x01", 12), b"ABCDEFGHABCD");
    }

    #[test]
    fn test_expand_does_not_overflow_output_size_when_expanding_previously_compressed_data() {
        assert_eq!(expand_impl(b"\xffABCDEFGH\0\x07\x01", 10), b"ABCDEFGHBC");
    }

    #[test]
    fn test_expand_inserts_spaces_when_compressed_data_references_negative_offset() {
        assert_eq!(
            expand_impl(b"\x0fABCD\x05\x0f", 22),
            b"ABCD                  "
        );
    }

    #[test]
    fn test_expand_stops_inserting_spaces_when_end_of_output_buffer_is_reached() {
        assert_eq!(expand_impl(b"\x0fABCD\x05\x0f", 10), b"ABCD      ");
    }

    #[test]
    fn test_expand_repeats_previous_data_when_length_extends_beyond_end_of_data() {
        assert_eq!(expand_impl(b"\x0fABCD\x02\x07", 14), b"ABCDCDCDCDCDCD");
    }

    #[test]
    fn test_expand_does_not_repeat_to_insert_more_than_requested_number_of_characters() {
        assert_eq!(expand_impl(b"\x0fABCD\x02\x08", 15), b"ABCDCDCDCDCDCDC");
    }

    #[test]
    fn test_expand_does_not_overflow_capacity_on_overlapping_repeat() {
        // b"\x0fABCD\x02\x07" would expand to 14 bytes (ABCDCDCDCDCDCD), but capacity is 7
        let out = expand_impl(b"\x0fABCD\x02\x07", 7);
        assert_eq!(out, b"ABCDCDC");
        assert_eq!(out.len(), 7);
    }

    #[test]
    fn test_expand_terminates_safely_when_pointer_has_zero_offset() {
        // b"\x00\x00\x00" has flag 0 and ptr 0x0000 (rposi = 0), which must not infinite-loop
        let out = expand_impl(b"\x00\x00\x00", 10);
        assert_eq!(out, b"");
    }

    #[test]
    fn test_compute_checksum() {
        assert_eq!(compute_checksum(b"ABCDEFGH"), 0x224);
        assert_eq!(compute_checksum(b""), 0);

        // Verify wrapping addition (modulo 2^32)
        let large_buffer = vec![0xff; 16 * 1024]; // 16384 * 255 = 4,177,920
        assert_eq!(compute_checksum(&large_buffer), 16384 * 255);
    }
}
