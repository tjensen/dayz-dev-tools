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

#[pyfunction]
fn expand<'p>(
    py: Python<'p>,
    input: &'p Bound<'p, PyBytes>,
    capacity: usize,
) -> PyResult<Bound<'p, PyBytes>> {
    let mut raw = InBuffer::<'p>::new(input.as_bytes());
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
    Ok(PyBytes::new(py, &output))
}

#[pymodule]
fn dayz_dev_tools_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(expand, m)?)
}
