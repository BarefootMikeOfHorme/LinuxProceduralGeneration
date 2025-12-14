//! PyO3 Python bindings for VaultMind Forge Core
//!
//! This module exposes Rust geometry operations to Python via PyO3.
//!
//! # Example Usage (Python):
//!
//! ```python
//! import vaultmind_forge_core as vf
//!
//! # Create primitives
//! box = vf.create_box((10.0, 10.0, 10.0))
//! sphere = vf.create_sphere(6.0)
//!
//! # CSG operations
//! result = vf.csg_difference(box, sphere)
//!
//! # Export
//! vf.export_mesh(result, "chamber.obj", "obj")
//! ```

use pyo3::prelude::*;
use pyo3::types::PyTuple;
use crate::geometry::{Mesh as RustMesh, Primitive};
use crate::geometry::primitives::{Box, Sphere, Cylinder};
use crate::csg::{union, difference, intersection};
use crate::export::{export, ExportFormat};
use nalgebra::{Point3, Vector3};
use std::path::PathBuf;

/// Python-wrapped Mesh
#[pyclass(name = "Mesh")]
#[derive(Clone)]
pub struct PyMesh {
    inner: RustMesh,
}

#[pymethods]
impl PyMesh {
    /// Get vertex count
    #[getter]
    fn vertex_count(&self) -> usize {
        self.inner.vertex_count()
    }

    /// Get triangle count
    #[getter]
    fn triangle_count(&self) -> usize {
        self.inner.triangle_count()
    }

    /// Get bounding box as ((min_x, min_y, min_z), (max_x, max_y, max_z))
    fn bounding_box(&self) -> ((f32, f32, f32), (f32, f32, f32)) {
        let (min, max) = self.inner.bounding_box();
        ((min.x, min.y, min.z), (max.x, max.y, max.z))
    }

    /// Export mesh to file
    fn export(&self, path: String, format: String) -> PyResult<()> {
        let export_format = match format.as_str() {
            "obj" => ExportFormat::Obj,
            "fbx" => ExportFormat::Fbx,
            "gltf" => ExportFormat::Gltf,
            _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("Unknown export format: {}", format)
            )),
        };

        export(&self.inner, &PathBuf::from(path), export_format)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(())
    }

    fn __repr__(&self) -> String {
        format!(
            "Mesh(vertices={}, triangles={})",
            self.vertex_count(),
            self.triangle_count()
        )
    }
}

/// Create a box primitive
#[pyfunction]
#[pyo3(signature = (size, center=None))]
fn create_box(size: (f32, f32, f32), center: Option<(f32, f32, f32)>) -> PyResult<PyMesh> {
    let mut b = Box::new(Vector3::new(size.0, size.1, size.2));

    if let Some((x, y, z)) = center {
        b = b.with_center(Point3::new(x, y, z));
    }

    let mesh = b.to_mesh()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(PyMesh { inner: mesh })
}

/// Create a sphere primitive
#[pyfunction]
#[pyo3(signature = (radius, center=None, segments=32, rings=16))]
fn create_sphere(
    radius: f32,
    center: Option<(f32, f32, f32)>,
    segments: u32,
    rings: u32,
) -> PyResult<PyMesh> {
    let mut s = Sphere::new(radius).with_detail(segments, rings);

    if let Some((x, y, z)) = center {
        s = s.with_center(Point3::new(x, y, z));
    }

    let mesh = s.to_mesh()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(PyMesh { inner: mesh })
}

/// Create a cylinder primitive
#[pyfunction]
#[pyo3(signature = (radius, height, center=None, segments=32))]
fn create_cylinder(
    radius: f32,
    height: f32,
    center: Option<(f32, f32, f32)>,
    segments: u32,
) -> PyResult<PyMesh> {
    let mut c = Cylinder::new(radius, height).with_segments(segments);

    if let Some((x, y, z)) = center {
        c = c.with_center(Point3::new(x, y, z));
    }

    let mesh = c.to_mesh()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(PyMesh { inner: mesh })
}

/// CSG Union operation
#[pyfunction]
fn csg_union(mesh_a: &PyMesh, mesh_b: &PyMesh) -> PyResult<PyMesh> {
    let result = union(&mesh_a.inner, &mesh_b.inner)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(PyMesh { inner: result })
}

/// CSG Difference operation
#[pyfunction]
fn csg_difference(mesh_a: &PyMesh, mesh_b: &PyMesh) -> PyResult<PyMesh> {
    let result = difference(&mesh_a.inner, &mesh_b.inner)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(PyMesh { inner: result })
}

/// CSG Intersection operation
#[pyfunction]
fn csg_intersection(mesh_a: &PyMesh, mesh_b: &PyMesh) -> PyResult<PyMesh> {
    let result = intersection(&mesh_a.inner, &mesh_b.inner)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(PyMesh { inner: result })
}

// PyO3 0.22 compatible module definition
#[pymodule]
fn vaultmind_forge_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyMesh>()?;

    // Primitive creation functions
    m.add_function(wrap_pyfunction!(create_box, m)?)?;
    m.add_function(wrap_pyfunction!(create_sphere, m)?)?;
    m.add_function(wrap_pyfunction!(create_cylinder, m)?)?;

    // CSG operations
    m.add_function(wrap_pyfunction!(csg_union, m)?)?;
    m.add_function(wrap_pyfunction!(csg_difference, m)?)?;
    m.add_function(wrap_pyfunction!(csg_intersection, m)?)?;

    // Version info
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("__author__", env!("CARGO_PKG_AUTHORS"))?;

    Ok(())
}
