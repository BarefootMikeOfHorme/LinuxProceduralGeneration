//! VaultMind Forge Core - High-Performance Geometry and Procedural Generation Engine
//!
//! This library provides Rust-powered geometry operations, CSG (Constructive Solid Geometry),
//! mesh processing, and procedural generation algorithms with Python bindings via PyO3.
//!
//! # Architecture
//!
//! - **geometry**: Primitive shapes (box, sphere, cylinder, etc.)
//! - **csg**: Boolean operations (union, difference, intersection)
//! - **mesh**: Mesh operations (optimization, LOD, subdivision)
//! - **export**: Multi-format export (OBJ, FBX, glTF, engine-specific)
//! - **python_bindings**: PyO3 interface for Python integration
//!
//! # Example (from Python)
//!
//! ```python
//! from vaultmind_forge import geometry
//!
//! # Create primitives
//! base = geometry.box(size=(10, 10, 10))
//! cutout = geometry.sphere(radius=6)
//!
//! # CSG operations
//! result = geometry.difference(base, cutout)
//!
//! # Export
//! result.export("chamber.fbx", engine="unity")
//! ```

// Core modules
pub mod geometry;
pub mod csg;
pub mod mesh;
pub mod export;

#[cfg(feature = "python-bindings")]
pub mod python_bindings;

// Re-exports


pub use geometry::{Primitive, Box, Sphere, Cylinder, Cone, Mesh};

pub use mesh::{MeshOptimizer, LodGenerator};

// Error types
use thiserror::Error;

#[derive(Error, Debug)]
pub enum GeometryError {
    #[error("Invalid geometry parameters: {0}")]
    InvalidParameters(String),

    #[error("CSG operation failed: {0}")]
    CsgOperationFailed(String),

    #[error("Mesh processing error: {0}")]
    MeshProcessingError(String),

    #[error("Export error: {0}")]
    ExportError(String),

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
}

pub type Result<T> = std::result::Result<T, GeometryError>;

// Version information
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
pub const AUTHORS: &str = env!("CARGO_PKG_AUTHORS");

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_version() {
        assert!(!VERSION.is_empty());
    }
}
