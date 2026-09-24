//! Engine-specific export bindings for Python

use pyo3::prelude::*;
use crate::export::engine_formats::{Engine as RustEngine, export_for_engine};
use super::PyMesh;
use std::path::PathBuf;

/// Export mesh with engine-specific transformations
#[pyfunction]
pub fn export_for_unity(mesh: &PyMesh, path: String) -> PyResult<()> {
    export_for_engine(&mesh.inner, &PathBuf::from(path), RustEngine::Unity)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(())
}

#[pyfunction]
pub fn export_for_unreal(mesh: &PyMesh, path: String) -> PyResult<()> {
    export_for_engine(&mesh.inner, &PathBuf::from(path), RustEngine::Unreal)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(())
}

#[pyfunction]
pub fn export_for_cryengine(mesh: &PyMesh, path: String) -> PyResult<()> {
    export_for_engine(&mesh.inner, &PathBuf::from(path), RustEngine::CryEngine)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(())
}

#[pyfunction]
pub fn export_for_lumix(mesh: &PyMesh, path: String) -> PyResult<()> {
    export_for_engine(&mesh.inner, &PathBuf::from(path), RustEngine::Lumix)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(())
}

#[pyfunction]
pub fn export_for_godot(mesh: &PyMesh, path: String) -> PyResult<()> {
    export_for_engine(&mesh.inner, &PathBuf::from(path), RustEngine::Godot)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(())
}

/// Get engine coordinate info
#[pyfunction]
pub fn get_unity_transform() -> ((f32, f32, f32, f32), (f32, f32, f32, f32), (f32, f32, f32, f32), (f32, f32, f32, f32)) {
    let m = RustEngine::Unity.transform_matrix();
    (
        (m[(0,0)], m[(0,1)], m[(0,2)], m[(0,3)]),
        (m[(1,0)], m[(1,1)], m[(1,2)], m[(1,3)]),
        (m[(2,0)], m[(2,1)], m[(2,2)], m[(2,3)]),
        (m[(3,0)], m[(3,1)], m[(3,2)], m[(3,3)]),
    )
}

#[pyfunction]
pub fn get_unreal_transform() -> ((f32, f32, f32, f32), (f32, f32, f32, f32), (f32, f32, f32, f32), (f32, f32, f32, f32)) {
    let m = RustEngine::Unreal.transform_matrix();
    (
        (m[(0,0)], m[(0,1)], m[(0,2)], m[(0,3)]),
        (m[(1,0)], m[(1,1)], m[(1,2)], m[(1,3)]),
        (m[(2,0)], m[(2,1)], m[(2,2)], m[(2,3)]),
        (m[(3,0)], m[(3,1)], m[(3,2)], m[(3,3)]),
    )
}

/// Register engine export functions with Python module
pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(export_for_unity, m)?)?;
    m.add_function(wrap_pyfunction!(export_for_unreal, m)?)?;
    m.add_function(wrap_pyfunction!(export_for_cryengine, m)?)?;
    m.add_function(wrap_pyfunction!(export_for_lumix, m)?)?;
    m.add_function(wrap_pyfunction!(export_for_godot, m)?)?;
    m.add_function(wrap_pyfunction!(get_unity_transform, m)?)?;
    m.add_function(wrap_pyfunction!(get_unreal_transform, m)?)?;
    Ok(())
}
