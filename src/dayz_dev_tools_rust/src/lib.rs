use pyo3::prelude::{pymodule, PyModule, PyResult};
use pyo3::types::PyModuleMethods;
use pyo3::{wrap_pyfunction, Bound};

mod expand;

#[pymodule]
fn dayz_dev_tools_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(expand::expand, m)?)
}
