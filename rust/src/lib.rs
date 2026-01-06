use pyo3::prelude::*;

// Minimal PyO3 module for Phase 1
// Will be expanded in later phases for search, markdown parsing, etc.

#[pymodule]
fn nanochat_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(greet, m)?)?;
    Ok(())
}

#[pyfunction]
fn greet(name: &str) -> String {
    format!("Hello from Rust, {}!", name)
}
