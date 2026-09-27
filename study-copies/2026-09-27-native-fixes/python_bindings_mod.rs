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

// Submodules
pub mod templates;
pub mod validation;
pub mod optimization;
pub mod engine_export;
use pyo3::prelude::*;
use pyo3::types::PyTuple;
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

    /// Vertex positions as a list of (x, y, z).
    ///
    /// Exposed so callers can verify topology directly instead of inferring it
    /// from a count. Positions stay welded, which is what makes a mesh usable for
    /// CSG and collision.
    #[getter]
    fn vertices(&self) -> Vec<(f32, f32, f32)> {
        self.inner
            .vertices
            .iter()
            .map(|v| (v.x, v.y, v.z))
            .collect()
    }

    /// Triangle indices, three per triangle.
    #[getter]
    fn indices(&self) -> Vec<u32> {
        self.inner.indices.clone()
    }

    /// Per-vertex normals as (x, y, z).
    ///
    /// These are the topology normals, averaged across adjacent faces, so a hard
    /// edge needs a marked sharp edge to survive. Use `split_for_render` for the
    /// flat-or-smooth form a renderer wants.
    #[getter]
    fn normals(&self) -> Vec<(f32, f32, f32)> {
        self.inner
            .normals
            .iter()
            .map(|n| (n.x, n.y, n.z))
            .collect()
    }

    /// Per-vertex UV coordinates as (u, v).
    ///
    /// A single UV per vertex cannot express a seam, so a box or cylinder reports
    /// zeros here while `face_uvs` carries the real mapping. Use
    /// `split_for_render`, which prefers `face_uvs`, when you want usable UVs.
    #[getter]
    fn uvs(&self) -> Vec<(f32, f32)> {
        self.inner.uvs.clone()
    }

    /// Per-face-corner UVs, three (u, v) pairs per triangle, or empty when the
    /// mesh has no per-corner mapping.
    #[getter]
    fn face_uvs(&self) -> Vec<Vec<(f32, f32)>> {
        self.inner
            .face_uvs
            .iter()
            .map(|tri| vec![tri[0], tri[1], tri[2]])
            .collect()
    }

    /// Number of edges marked sharp, the edges smoothing must not cross.
    #[getter]
    fn sharp_edge_count(&self) -> usize {
        self.inner.sharp_edges.len()
    }

    /// Derive the render form: positions duplicated wherever a crease or a UV
    /// seam needs it, with exactly one normal and one UV per output vertex.
    ///
    /// `smooth_angle_degrees` is the auto-smooth threshold. 180.0 smooths
    /// everything not explicitly marked sharp, 0.0 flattens everything.
    fn split_for_render(&self, smooth_angle_degrees: f32) -> PyRenderMesh {
        PyRenderMesh {
            inner: self.inner.split_for_render(smooth_angle_degrees),
        }
    }

    /// Derive the render form, merging corners on `(position, normal, uv)`
    /// compared bit for bit.
    ///
    /// This is MikkTSpace's rule and the rule glTF's reference cube obeys:
    /// `Box.gltf` ships 24 positions for 36 indices. `split_for_render` keys on
    /// the smoothing group, so the two triangles of a coplanar quad are always
    /// different groups and never merge; it emits 36 for the same box. Measured
    /// across this crate's primitives:
    ///
    ///     box       36 -> 24      sphere    2790 -> 2782   (at 0 degrees)
    ///     cylinder 322 -> 194      cone       177 -> 176
    ///     torus    6832 -> 6784
    ///
    /// At a smoothing angle the mesh actually uses, the two agree: a sphere at
    /// 30 degrees is 482 either way, because a sphere has no creases to split
    /// and no quad to merge.
    ///
    /// The comparison is exact on purpose and there is no tolerance parameter to
    /// pass. Quantising the normal onto a grid of step `h` merges normals up to
    /// `h / sqrt(3)` apart, which at `h = 1e-2` is 0.33 degrees: enough to
    /// swallow a crease and produce shading nobody can trace. A crease survives
    /// here because its two normals are not the same bits.
    fn split_for_render_keyed(&self, smooth_angle_degrees: f32) -> PyRenderMesh {
        PyRenderMesh {
            inner: self.inner.split_for_render_keyed(smooth_angle_degrees),
        }
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

    /// Export mesh to OBJ file (convenience method)
    fn export_obj(&self, path: String) -> PyResult<()> {
        export(&self.inner, &PathBuf::from(path), ExportFormat::Obj)
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

/// A render-ready mesh produced by `PyMesh::split_for_render`.
///
/// A separate type on purpose. A render mesh is not manifold, so handing one back
/// to something expecting welded topology would quietly break CSG and collision;
/// keeping the types distinct makes that a mistake the compiler catches.
#[pyclass]
pub struct PyRenderMesh {
    inner: crate::geometry::RenderMesh,
}

#[pymethods]
impl PyRenderMesh {
    /// Number of output vertices, larger than the source wherever a split
    /// happened.
    #[getter]
    fn vertex_count(&self) -> usize {
        self.inner.vertex_count()
    }

    /// Number of triangles. Equal to the source mesh: splitting duplicates
    /// vertices, it never changes topology.
    #[getter]
    fn triangle_count(&self) -> usize {
        self.inner.triangle_count()
    }

    /// How many distinct positions the mesh occupies, which is the source
    /// mesh's vertex count when no split was needed.
    #[getter]
    fn unique_position_count(&self) -> usize {
        self.inner.unique_position_count()
    }

    /// Output vertex positions as (x, y, z).
    #[getter]
    fn vertices(&self) -> Vec<(f32, f32, f32)> {
        self.inner
            .vertices
            .iter()
            .map(|v| (v.x, v.y, v.z))
            .collect()
    }

    /// One normal per output vertex as (x, y, z).
    #[getter]
    fn normals(&self) -> Vec<(f32, f32, f32)> {
        self.inner
            .normals
            .iter()
            .map(|n| (n.x, n.y, n.z))
            .collect()
    }

    /// One UV per output vertex as (u, v).
    #[getter]
    fn uvs(&self) -> Vec<(f32, f32)> {
        self.inner.uvs.clone()
    }

    /// Triangle indices over the output vertices.
    #[getter]
    fn indices(&self) -> Vec<u32> {
        self.inner.indices.clone()
    }

    fn __repr__(&self) -> String {
        format!(
            "RenderMesh(vertices={}, triangles={}, unique_positions={})",
            self.vertex_count(),
            self.triangle_count(),
            self.unique_position_count()
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


/// Create a cone primitive
#[pyfunction]
#[pyo3(signature = (radius, height, center=None, segments=32))]
fn create_cone(
    radius: f32,
    height: f32,
    center: Option<(f32, f32, f32)>,
    segments: u32,
) -> PyResult<PyMesh> {
    let mut c = Cone::new(radius, height).with_segments(segments);

    if let Some((x, y, z)) = center {
        c = c.with_center(Point3::new(x, y, z));
    }

    let mesh = c.to_mesh()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

/// Create a torus primitive
#[pyfunction]
#[pyo3(signature = (major_radius, minor_radius, center=None, major_segments=48, minor_segments=24))]
fn create_torus(
    major_radius: f32,
    minor_radius: f32,
    center: Option<(f32, f32, f32)>,
    major_segments: u32,
    minor_segments: u32,
) -> PyResult<PyMesh> {
    let mut t = Torus::new(major_radius, minor_radius).with_segments(major_segments, minor_segments);

    if let Some((x, y, z)) = center {
        t = t.with_center(Point3::new(x, y, z));
    }

    let mesh = t.to_mesh()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

/// Create a capsule primitive
#[pyfunction]
#[pyo3(signature = (radius, height, rings=8, segments=16))]
fn create_capsule(radius: f32, height: f32, rings: usize, segments: usize) -> PyResult<PyMesh> {
    let c = Capsule::new(radius, height).with_detail(rings, segments);
    let mesh = c.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

/// Create a pyramid primitive
#[pyfunction]
#[pyo3(signature = (base_size, height))]
fn create_pyramid(base_size: f32, height: f32) -> PyResult<PyMesh> {
    let p = Pyramid::new(base_size, height);
    let mesh = p.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

/// Create a plane primitive
#[pyfunction]
#[pyo3(signature = (width, depth))]
fn create_plane(width: f32, depth: f32) -> PyResult<PyMesh> {
    let p = Plane::new(width, depth);
    let mesh = p.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

/// Create a disc primitive
#[pyfunction]
#[pyo3(signature = (radius,))]
fn create_disc(radius: f32) -> PyResult<PyMesh> {
    let d = Disc::new(radius);
    let mesh = d.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

/// Create a ring primitive
#[pyfunction]
#[pyo3(signature = (inner_radius, outer_radius))]
fn create_ring(inner_radius: f32, outer_radius: f32) -> PyResult<PyMesh> {
    let r = Ring::new(inner_radius, outer_radius);
    let mesh = r.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

/// Create a tube primitive
#[pyfunction]
#[pyo3(signature = (inner_radius, outer_radius, height))]
fn create_tube(inner_radius: f32, outer_radius: f32, height: f32) -> PyResult<PyMesh> {
    let t = Tube::new(inner_radius, outer_radius, height);
    let mesh = t.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

/// Create a prism primitive (3, 6, or 8 sided)
#[pyfunction]
#[pyo3(signature = (radius, height, sides))]
fn create_prism(radius: f32, height: f32, sides: usize) -> PyResult<PyMesh> {
    let p = match sides {
        3 => Prism::triangular(radius, height),
        6 => Prism::hexagonal(radius, height),
        8 => Prism::octagonal(radius, height),
        _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Prism only supports 3, 6, or 8 sides")),
    };
    let mesh = p.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

/// Create a dome primitive
#[pyfunction]
#[pyo3(signature = (radius,))]
fn create_dome(radius: f32) -> PyResult<PyMesh> {
    let d = Dome::new(radius);
    let mesh = d.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

/// Create a tetrahedron primitive
#[pyfunction]
#[pyo3(signature = (size,))]
fn create_tetrahedron(size: f32) -> PyResult<PyMesh> {
    let t = Tetrahedron::new(size);
    let mesh = t.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

/// Create an octahedron primitive
#[pyfunction]
#[pyo3(signature = (size,))]
fn create_octahedron(size: f32) -> PyResult<PyMesh> {
    let o = Octahedron::new(size);
    let mesh = o.to_mesh().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(PyMesh { inner: mesh })
}

/// Load a triangulated mesh from an OBJ file.
#[pyfunction]
fn load_obj(path: String) -> PyResult<PyMesh> {
    let mesh = crate::mesh::obj::load_obj(&PathBuf::from(path))
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
    m.add_class::<PyRenderMesh>()?;

    // Primitive creation functions
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

    // Mesh import
    m.add_function(wrap_pyfunction!(load_obj, m)?)?;

    // CSG operations
    m.add_function(wrap_pyfunction!(csg_union, m)?)?;
    m.add_function(wrap_pyfunction!(csg_difference, m)?)?;
    m.add_function(wrap_pyfunction!(csg_intersection, m)?)?;

    // Version info
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("__author__", env!("CARGO_PKG_AUTHORS"))?;

    // Register submodules
    templates::register(m)?;
    validation::register(m)?;
    optimization::register(m)?;
    engine_export::register(m)?;

    Ok(())
}
