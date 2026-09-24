"""Write comprehensive Python bindings for Rust core"""

BINDINGS_CONTENT = r'''//! PyO3 Python bindings for VaultMind Forge Core
//!
//! Exposes all Rust geometry functionality to Python

use pyo3::prelude::*;
use crate::geometry::{Mesh as RustMesh, Primitive};
use crate::geometry::primitives::{Box, Sphere, Cylinder, Cone, Torus};
use crate::geometry::extended_primitives::{
    Capsule, Pyramid, Plane, Disc, Ring, Tube, Prism, Dome, Tetrahedron, Octahedron
};
use crate::csg::{union, difference, intersection};
use crate::export::{export, ExportFormat};
use nalgebra::{Point3, Vector3};
use std::path::PathBuf;

/// Python-wrapped Mesh
#[pyclass(name = "Mesh")]
#[derive(Clone)]
pub struct PyMesh {
    pub(crate) inner: RustMesh,
}

#[pymethods]
impl PyMesh {
    #[getter]
    fn vertex_count(&self) -> usize {
        self.inner.vertex_count()
    }

    #[getter]
    fn triangle_count(&self) -> usize {
        self.inner.triangle_count()
    }

    fn bounding_box(&self) -> ((f32, f32, f32), (f32, f32, f32)) {
        let (min, max) = self.inner.bounding_box();
        ((min.x, min.y, min.z), (max.x, max.y, max.z))
    }

    fn export(&self, path: String, format: String) -> PyResult<()> {
        let export_format = match format.as_str() {
            "obj" => ExportFormat::Obj,
            "fbx" => ExportFormat::Fbx,
            "gltf" => ExportFormat::Gltf,
            "unity" => ExportFormat::Unity,
            "godot" => ExportFormat::Godot,
            "unreal" => ExportFormat::Unreal,
            _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("Unknown format: {}", format)
            )),
        };

        export(&self.inner, &PathBuf::from(path), export_format)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(())
    }

    fn __repr__(&self) -> String {
        format!("Mesh(vertices={}, triangles={})", self.vertex_count(), self.triangle_count())
    }
}

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

#[pyfunction]
#[pyo3(signature = (radius, center=None, segments=32, rings=16))]
fn create_sphere(radius: f32, center: Option<(f32, f32, f32)>, segments: u32, rings: u32) -> PyResult<PyMesh> {
    let mut s = Sphere::new(radius).with_detail(segments, rings);
    if let Some((x, y, z)) = center {
        s = s.with_center(Point3::new(x, y, z));
    }
    let mesh = s.to_mesh()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

#[pyfunction]
#[pyo3(signature = (radius, height, center=None, segments=32))]
fn create_cylinder(radius: f32, height: f32, center: Option<(f32, f32, f32)>, segments: u32) -> PyResult<PyMesh> {
    let mut c = Cylinder::new(radius, height).with_segments(segments);
    if let Some((x, y, z)) = center {
        c = c.with_center(Point3::new(x, y, z));
    }
    let mesh = c.to_mesh()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

#[pyfunction]
#[pyo3(signature = (radius, height, center=None, segments=32))]
fn create_cone(radius: f32, height: f32, center: Option<(f32, f32, f32)>, segments: u32) -> PyResult<PyMesh> {
    let mut c = Cone::new(radius, height).with_segments(segments);
    if let Some((x, y, z)) = center {
        c = c.with_center(Point3::new(x, y, z));
    }
    let mesh = c.to_mesh()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

#[pyfunction]
#[pyo3(signature = (major_radius, minor_radius, center=None, major_segments=32, minor_segments=16))]
fn create_torus(major_radius: f32, minor_radius: f32, center: Option<(f32, f32, f32)>, major_segments: u32, minor_segments: u32) -> PyResult<PyMesh> {
    let mut t = Torus::new(major_radius, minor_radius).with_detail(major_segments, minor_segments);
    if let Some((x, y, z)) = center {
        t = t.with_center(Point3::new(x, y, z));
    }
    let mesh = t.to_mesh()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

#[pyfunction]
#[pyo3(signature = (radius, height, rings=8, segments=16))]
fn create_capsule(radius: f32, height: f32, rings: usize, segments: usize) -> PyResult<PyMesh> {
    let c = Capsule::new(radius, height, rings, segments);
    let mesh = c.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

#[pyfunction]
#[pyo3(signature = (base_size, height, sides=4))]
fn create_pyramid(base_size: f32, height: f32, sides: usize) -> PyResult<PyMesh> {
    let p = Pyramid::new(base_size, height, sides);
    let mesh = p.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

#[pyfunction]
#[pyo3(signature = (width, depth, width_segments=1, depth_segments=1))]
fn create_plane(width: f32, depth: f32, width_segments: usize, depth_segments: usize) -> PyResult<PyMesh> {
    let p = Plane::new(width, depth, width_segments, depth_segments);
    let mesh = p.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

#[pyfunction]
#[pyo3(signature = (radius, segments=32))]
fn create_disc(radius: f32, segments: usize) -> PyResult<PyMesh> {
    let d = Disc::new(radius, segments);
    let mesh = d.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

#[pyfunction]
#[pyo3(signature = (inner_radius, outer_radius, segments=32))]
fn create_ring(inner_radius: f32, outer_radius: f32, segments: usize) -> PyResult<PyMesh> {
    let r = Ring::new(inner_radius, outer_radius, segments);
    let mesh = r.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

#[pyfunction]
#[pyo3(signature = (inner_radius, outer_radius, height, segments=32))]
fn create_tube(inner_radius: f32, outer_radius: f32, height: f32, segments: usize) -> PyResult<PyMesh> {
    let t = Tube::new(inner_radius, outer_radius, height, segments);
    let mesh = t.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

#[pyfunction]
#[pyo3(signature = (radius, height, sides))]
fn create_prism(radius: f32, height: f32, sides: usize) -> PyResult<PyMesh> {
    let p = Prism::new(radius, height, sides);
    let mesh = p.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

#[pyfunction]
#[pyo3(signature = (radius, rings=8, segments=16))]
fn create_dome(radius: f32, rings: usize, segments: usize) -> PyResult<PyMesh> {
    let d = Dome::new(radius, rings, segments);
    let mesh = d.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

#[pyfunction]
#[pyo3(signature = (size,))]
fn create_tetrahedron(size: f32) -> PyResult<PyMesh> {
    let t = Tetrahedron::new(size);
    let mesh = t.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

#[pyfunction]
#[pyo3(signature = (size,))]
fn create_octahedron(size: f32) -> PyResult<PyMesh> {
    let o = Octahedron::new(size);
    let mesh = o.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

#[pyfunction]
fn csg_union(mesh_a: &PyMesh, mesh_b: &PyMesh) -> PyResult<PyMesh> {
    let result = union(&mesh_a.inner, &mesh_b.inner)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: result })
}

#[pyfunction]
fn csg_difference(mesh_a: &PyMesh, mesh_b: &PyMesh) -> PyResult<PyMesh> {
    let result = difference(&mesh_a.inner, &mesh_b.inner)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: result })
}

#[pyfunction]
fn csg_intersection(mesh_a: &PyMesh, mesh_b: &PyMesh) -> PyResult<PyMesh> {
    let result = intersection(&mesh_a.inner, &mesh_b.inner)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: result })
}

#[pymodule]
fn vaultmind_forge_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyMesh>()?;

    m.add_function(wrap_pyfunction!(create_box, m)?)?;
    m.add_function(wrap_pyfunction!(create_sphere, m)?)?;
    m.add_function(wrap_pyfunction!(create_cylinder, m)?)?;
    m.add_function(wrap_pyfunction!(create_cone, m)?)?;
    m.add_function(wrap_pyfunction!(create_torus, m)?)?;
    m.add_function(wrap_pyfunction!(create_capsule, m)?)?;
    m.add_function(wrap_pyfunction!(create_pyramid, m)?)?;
    m.add_function(wrap_pyfunction!(create_plane, m)?)?;
    m.add_function(wrap_pyfunction!(create_disc, m)?)?;
    m.add_function(wrap_pyfunction!(create_ring, m)?)?;
    m.add_function(wrap_pyfunction!(create_tube, m)?)?;
    m.add_function(wrap_pyfunction!(create_prism, m)?)?;
    m.add_function(wrap_pyfunction!(create_dome, m)?)?;
    m.add_function(wrap_pyfunction!(create_tetrahedron, m)?)?;
    m.add_function(wrap_pyfunction!(create_octahedron, m)?)?;
    m.add_function(wrap_pyfunction!(csg_union, m)?)?;
    m.add_function(wrap_pyfunction!(csg_difference, m)?)?;
    m.add_function(wrap_pyfunction!(csg_intersection, m)?)?;

    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("__author__", env!("CARGO_PKG_AUTHORS"))?;

    Ok(())
}

pub mod templates;
pub mod validation;
pub mod optimization;
pub mod engine_export;
'''

if __name__ == "__main__":
    output_path = "rust_core/src/python_bindings/mod.rs"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(BINDINGS_CONTENT)
    print(f"[OK] Written {len(BINDINGS_CONTENT)} characters to {output_path}")
