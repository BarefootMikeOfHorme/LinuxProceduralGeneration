//! Constructive Solid Geometry (CSG) Operations
//!
//! Production-quality boolean operations with robust algorithms:
//! - Triangle-triangle intersection using parry3d
//! - Inside/outside classification with ray casting  
//! - Edge clipping at boundaries
//! - Degenerate case handling

pub mod robust;

use crate::geometry::Mesh;
use crate::{Result, GeometryError};
pub use robust::RobustCsgEngine;

/// CSG operation types
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CsgOperation {
    Union,
    Difference,
    Intersection,
}

/// Perform CSG union: A ∪ B (combine two meshes) - ROBUST VERSION
pub fn union(mesh_a: &Mesh, mesh_b: &Mesh) -> Result<Mesh> {
    let engine = RobustCsgEngine::new();
    engine.union(mesh_a, mesh_b)
}

/// Perform CSG difference: A \ B (subtract B from A) - ROBUST VERSION  
pub fn difference(mesh_a: &Mesh, mesh_b: &Mesh) -> Result<Mesh> {
    let engine = RobustCsgEngine::new();
    engine.difference(mesh_a, mesh_b)
}

/// Perform CSG intersection: A ∩ B (keep only overlapping volume) - ROBUST VERSION
pub fn intersection(mesh_a: &Mesh, mesh_b: &Mesh) -> Result<Mesh> {
    let engine = RobustCsgEngine::new();
    engine.intersection(mesh_a, mesh_b)
}

/// Generic CSG operation dispatcher
pub fn csg_operation(
    mesh_a: &Mesh,
    mesh_b: &Mesh,
    operation: CsgOperation,
) -> Result<Mesh> {
    match operation {
        CsgOperation::Union => union(mesh_a, mesh_b),
        CsgOperation::Difference => difference(mesh_a, mesh_b),
        CsgOperation::Intersection => intersection(mesh_a, mesh_b),
    }
}
