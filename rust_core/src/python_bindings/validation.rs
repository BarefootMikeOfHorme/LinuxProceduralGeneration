//! Mesh validation and repair bindings for Python

use pyo3::prelude::*;
use crate::mesh::validation::{MeshValidator as RustValidator, ValidationReport as RustReport};
use super::PyMesh;

/// Python-wrapped validation report
#[pyclass(name = "ValidationReport")]
#[derive(Clone)]
pub struct PyValidationReport {
    inner: RustReport,
}

#[pymethods]
impl PyValidationReport {
    #[getter]
    fn is_valid(&self) -> bool {
        self.inner.is_valid
    }

    #[getter]
    fn is_manifold(&self) -> bool {
        self.inner.is_manifold
    }

    #[getter]
    fn is_watertight(&self) -> bool {
        self.inner.is_watertight
    }

    #[getter]
    fn has_self_intersections(&self) -> Option<bool> {
        self.inner.has_self_intersections
    }

    #[getter]
    fn degenerate_triangle_count(&self) -> usize {
        self.inner.degenerate_triangle_count
    }

    #[getter]
    fn duplicate_vertex_count(&self) -> usize {
        self.inner.duplicate_vertex_count
    }

    #[getter]
    fn non_manifold_edge_count(&self) -> usize {
        self.inner.non_manifold_edge_count
    }

    #[getter]
    fn hole_count(&self) -> usize {
        self.inner.hole_count
    }

    #[getter]
    fn issues(&self) -> Vec<String> {
        self.inner.issues.clone()
    }

    fn __repr__(&self) -> String {
        format!("ValidationReport(valid={}, manifold={}, watertight={}, self_intersections={:?}, issues={})",
            self.inner.is_valid,
            self.inner.is_manifold,
            self.inner.is_watertight,
            self.inner.has_self_intersections,
            self.inner.issues.len())
    }
}

/// Python-wrapped mesh validator
#[pyclass(name = "MeshValidator")]
pub struct PyMeshValidator {
    inner: RustValidator,
}

#[pymethods]
impl PyMeshValidator {
    #[new]
    fn new() -> Self {
        Self {
            inner: RustValidator::new(),
        }
    }

    /// Create validator with custom tolerance
    #[staticmethod]
    fn with_tolerance(merge_distance: f32, epsilon: f32) -> Self {
        Self {
            inner: RustValidator::with_tolerance(merge_distance, epsilon),
        }
    }

    /// Validate a mesh
    fn validate(&self, mesh: &PyMesh) -> PyValidationReport {
        let report = self.inner.validate(&mesh.inner);
        PyValidationReport { inner: report }
    }

    /// Repair a mesh
    fn repair(&self, mesh: &PyMesh) -> PyResult<PyMesh> {
        let repaired = self.inner.repair(&mesh.inner)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(PyMesh { inner: repaired })
    }
}

/// Register validation functions with Python module
pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyValidationReport>()?;
    m.add_class::<PyMeshValidator>()?;
    Ok(())
}
