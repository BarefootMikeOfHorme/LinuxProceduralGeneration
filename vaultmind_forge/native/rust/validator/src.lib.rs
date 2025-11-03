use pyo3::prelude::*;

#[pyfunction]
fn rs_sharpness_score(_path: &str) -> PyResult<f32> { Ok(0.0) }

#[pymodule]
fn vmf_validator(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rs_sharpness_score, m)?)?;
    Ok(())
}