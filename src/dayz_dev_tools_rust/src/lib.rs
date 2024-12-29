use pyo3::prelude::{pyfunction, pymodule, PyModule, PyResult, Python};
use pyo3::types::{PyBytes, PyBytesMethods, PyModuleMethods};
use pyo3::{wrap_pyfunction, Bound};
use std::cmp::min;
use std::iter;

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
        Ok(self.readbyte()? as u16 | ((self.readbyte()? as u16) << 8))
    }
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

                    if rposi < output.len() {
                        let rpos = output.len() - rposi;

                        if rpos + rlen < output.len() {
                            output.extend_from_within(
                                rpos..min(rpos + rlen, rpos + capacity - output.len()),
                            );
                        } else {
                            while output.len() < rpos + rlen {
                                output.extend_from_within(
                                    rpos..(rpos
                                        + min(output.len() - rpos, capacity - output.len())),
                                );
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
    output
}

#[pyfunction]
fn expand<'p>(
    py: Python<'p>,
    input: &'p Bound<'p, PyBytes>,
    capacity: usize,
) -> PyResult<Bound<'p, PyBytes>> {
    let output = expand_impl(input.as_bytes(), capacity);

    Ok(PyBytes::new(py, &output))
}

#[pymodule]
fn dayz_dev_tools_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(expand, m)?)
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
}
