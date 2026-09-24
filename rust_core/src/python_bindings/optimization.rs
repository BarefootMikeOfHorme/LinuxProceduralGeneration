//! Advanced optimization bindings for Python
//! Exposes Tom Forsyth and QEM simplification

use pyo3::prelude::*;
use crate::mesh::advanced_optimizer::AdvancedOptimizer as RustOptimizer;
use super::PyMesh;

/// Python-wrapped advanced optimizer
#[pyclass(name = "AdvancedOptimizer")]
pub struct PyAdvancedOptimizer {
    inner: RustOptimizer,
}

#[pymethods]
impl PyAdvancedOptimizer {
    #[new]
    fn new() -> Self {
        Self {
            inner: RustOptimizer::new(),
        }
    }

    /// Create optimizer with custom cache size
    #[staticmethod]
    fn with_cache_size(cache_size: usize) -> Self {
        Self {
            inner: RustOptimizer::with_cache_size(cache_size),
        }
    }

    /// Optimize vertex cache using Tom Forsyth algorithm
    fn optimize_vertex_cache(&self, mesh: &PyMesh) -> PyResult<PyMesh> {
        let optimized = self.inner.optimize_vertex_cache(&mesh.inner)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(PyMesh { inner: optimized })
    }

    /// Simplify mesh using Quadric Error Metrics (QEM)
    fn simplify_qem(&self, mesh: &PyMesh, target_triangle_count: usize) -> PyResult<PyMesh> {
        let simplified = self.inner.simplify_qem(&mesh.inner, target_triangle_count)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(PyMesh { inner: simplified })
    }

    /// Calculate ACMR (Average Cache Miss Ratio)
    fn calculate_acmr(&self, mesh: &PyMesh) -> f32 {
        self.inner.calculate_acmr(&mesh.inner)
    }

    /// Calculate ATVR (Average Transform to Vertex Ratio)
    fn calculate_atvr(&self, mesh: &PyMesh) -> f32 {
        self.inner.calculate_atvr(&mesh.inner)
    }
}

/// Register optimization functions with Python module
pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyAdvancedOptimizer>()?;
    Ok(())
}
