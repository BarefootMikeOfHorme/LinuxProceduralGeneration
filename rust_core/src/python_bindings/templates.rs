//! Size template bindings for Python
//! Exposes game engine size templates

use pyo3::prelude::*;
use crate::geometry::templates::{SizeTemplate as RustTemplate, TemplateCategory, all_templates};

/// Python-wrapped size template
#[pyclass(name = "SizeTemplate")]
#[derive(Clone)]
pub struct PySizeTemplate {
    inner: RustTemplate,
}

#[pymethods]
impl PySizeTemplate {
    #[getter]
    fn name(&self) -> &str {
        self.inner.name
    }

    #[getter]
    fn description(&self) -> &str {
        self.inner.description
    }

    #[getter]
    fn size(&self) -> (f32, f32, f32) {
        (self.inner.size.x, self.inner.size.y, self.inner.size.z)
    }

    #[getter]
    fn category(&self) -> String {
        format!("{:?}", self.inner.category)
    }

    /// Get size for Unity (meters)
    fn for_unity(&self) -> (f32, f32, f32) {
        let v = self.inner.for_unity();
        (v.x, v.y, v.z)
    }

    /// Get size for Unreal Engine (centimeters)
    fn for_unreal(&self) -> (f32, f32, f32) {
        let v = self.inner.for_unreal();
        (v.x, v.y, v.z)
    }

    /// Get size for CryEngine (centimeters)
    fn for_cryengine(&self) -> (f32, f32, f32) {
        let v = self.inner.for_cryengine();
        (v.x, v.y, v.z)
    }

    /// Get size for Source Engine (custom units: 16u = 1 foot)
    fn for_source(&self) -> (f32, f32, f32) {
        let v = self.inner.for_source();
        (v.x, v.y, v.z)
    }

    /// Get size for Lumix Engine (meters)
    fn for_lumix(&self) -> (f32, f32, f32) {
        let v = self.inner.for_lumix();
        (v.x, v.y, v.z)
    }

    /// Get size for Godot (meters)
    fn for_godot(&self) -> (f32, f32, f32) {
        let v = self.inner.for_godot();
        (v.x, v.y, v.z)
    }

    fn __repr__(&self) -> String {
        format!("SizeTemplate('{}', size=({:.2}, {:.2}, {:.2})m)",
            self.inner.name,
            self.inner.size.x,
            self.inner.size.y,
            self.inner.size.z)
    }
}

/// Get all available size templates
#[pyfunction]
pub fn get_all_templates() -> Vec<PySizeTemplate> {
    all_templates()
        .into_iter()
        .map(|t| PySizeTemplate { inner: t })
        .collect()
}

/// Get templates by category
#[pyfunction]
pub fn get_templates_by_category(category: &str) -> Vec<PySizeTemplate> {
    let templates = all_templates();
    templates
        .into_iter()
        .filter(|t| format!("{:?}", t.category).to_lowercase() == category.to_lowercase())
        .map(|t| PySizeTemplate { inner: t })
        .collect()
}

/// Register template functions with Python module
pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PySizeTemplate>()?;
    m.add_function(wrap_pyfunction!(get_all_templates, m)?)?;
    m.add_function(wrap_pyfunction!(get_templates_by_category, m)?)?;
    Ok(())
}
