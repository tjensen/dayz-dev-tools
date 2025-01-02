use pyo3::exceptions::PyValueError;
use pyo3::prelude::{pyfunction, PyResult, Python};
use pyo3::types::{PyBytes, PyBytesMethods};
use pyo3::Bound;
use std::cmp::min;
use std::iter;

type Result<T> = std::result::Result<T, ChecksumError>;

#[derive(Debug, Clone)]
struct ChecksumError {
    message: String
}

impl ChecksumError {
    fn new(actual: u32, expected: u32) -> ChecksumError {
        ChecksumError {
            message: format!("Checksum mismatch ({:#x} != {:#x})", actual, expected)
        }
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
        self.i >= self.raw.len() - 4
    }

    fn readbyte(&mut self) -> std::result::Result<u8, &'static str> {
        if self.i >= self.raw.len() - 4 {
            return Err("end of input reached");
        }
        let result = self.raw[self.i];
        self.i += 1;
        Ok(result)
    }

    fn readword(&mut self) -> std::result::Result<u16, &'static str> {
        Ok(self.readbyte()? as u16 | ((self.readbyte()? as u16) << 8))
    }

    fn checksum(&self) -> u32 {
        u32::from_le_bytes(*self.raw.last_chunk::<4>().unwrap())
    }
}

fn expand_impl(inbytes: &[u8], capacity: usize) -> Result<Vec<u8>> {
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

                    if rposi <= output.len() {
                        let rpos = output.len() - rposi;

                        if rpos + rlen < output.len() {
                            output.extend_from_within(
                                rpos..min(rpos + rlen, rpos + capacity - output.len()),
                            );
                        } else {
                            let newlen = output.len() + rlen;
                            while output.len() < newlen {
                                let rend = rpos + min(output.len() - rpos, newlen - output.len());
                                output.extend_from_within(rpos..rend);
                            }
                        }
                    } else {
                        output.extend(iter::repeat_n(32u8, min(rlen, capacity - output.len())));
                    }
                } else {
                    break 'outer;
                }
            }
        } else {
            break 'outer;
        }
    }

    let checksum = output.iter().fold(0u32, |sum, b| sum + *b as u32);
    if raw.checksum() != checksum {
        Err(ChecksumError::new(checksum, raw.checksum()))
    }
    else {
        Ok(output)
    }
}

#[pyfunction]
pub fn expand<'p>(
    py: Python<'p>,
    input: &'p Bound<'p, PyBytes>,
    capacity: usize,
) -> PyResult<Bound<'p, PyBytes>> {
    match expand_impl(input.as_bytes(), capacity) {
        Ok(output) => Ok(PyBytes::new(py, &output)),
        Err(error) => Err(PyValueError::new_err(error.message)),
    }

}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_expand_expands_trivially_compressed_file() {
        assert_eq!(expand_impl(b"\xffABCDEFGH\xffIJKLMNOP\xffQRSTUVWX\x2c\x07\x00\x00", 24).unwrap(), b"ABCDEFGHIJKLMNOPQRSTUVWX");
    }

    #[test]
    fn test_expand_returns_error_when_expanded_data_does_not_match_checksum() {
        let err = expand_impl(b"\xffABCDEFGH\xffIJKLMNOP\xffQRSTUVWX\xff\xff\xff\xff", 24).unwrap_err();

        assert_eq!(err.message, "Checksum mismatch (0x72c != 0xffffffff)");
    }

    #[test]
    fn test_expand_stops_extracting_bytes_when_end_of_content_is_reached_within_packet() {
        assert_eq!(expand_impl(b"\xffABCDE\x4f\x01\x00\x00", 5).unwrap(), b"ABCDE");
    }

    #[test]
    fn test_expand_stops_extracting_bytes_when_end_of_output_buffer_is_reached() {
        assert_eq!(
            expand_impl(b"\xffABCDEFGH\xffIJKLMNOP\xffQRSTUVWX\x4f\x01\x00\x00", 5).unwrap(),
            b"ABCDE"
        );
    }

    #[test]
    fn test_expand_expands_previously_compressed_data() {
        assert_eq!(expand_impl(b"\xffABCDEFGH\0\x07\x01\x32\x03\x00\x00", 12).unwrap(), b"ABCDEFGHBCDE");
    }

    #[test]
    fn test_expand_repeats_characters_from_beginning_of_output() {
        assert_eq!(expand_impl(b"\xffABCDEFGH\0\x08\x01\x2e\x03\x00\x00", 12).unwrap(), b"ABCDEFGHABCD");
    }

    #[test]
    fn test_expand_does_not_overflow_output_size_when_expanding_previously_compressed_data() {
        assert_eq!(expand_impl(b"\xffABCDEFGH\0\x07\x01\xa9\x02\x00\x00", 10).unwrap(), b"ABCDEFGHBC");
    }

    #[test]
    fn test_expand_inserts_spaces_when_compressed_data_references_negative_offset() {
        assert_eq!(
            expand_impl(b"\x0fABCD\x05\x0f\x4a\x03\x00\x00", 22).unwrap(),
            b"ABCD                  "
        );
    }

    #[test]
    fn test_expand_stops_inserting_spaces_when_end_of_output_buffer_is_reached() {
        assert_eq!(expand_impl(b"\x0fABCD\x05\x0f\xca\x01\x00\x00", 10).unwrap(), b"ABCD      ");
    }

    #[test]
    fn test_expand_repeats_previous_data_when_length_extends_beyond_end_of_data() {
        assert_eq!(expand_impl(b"\x0fABCD\x02\x07\xad\x03\x00\x00", 14).unwrap(), b"ABCDCDCDCDCDCD");
    }

    #[test]
    fn test_expand_does_not_repeat_to_insert_more_than_requested_number_of_characters() {
        assert_eq!(expand_impl(b"\x0fABCD\x02\x08\xf0\x03\x00\x00", 15).unwrap(), b"ABCDCDCDCDCDCDC");
    }
}
