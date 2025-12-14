//! Mesh processing and optimization
//!
//! Inspired by Ice Engine's Meshmerizer: mesh cleaning, LOD generation,
//! compression, subdivision surfaces, convex hulls, etc.

use crate::geometry::Mesh;
use crate::{Result, GeometryError};
use rayon::prelude::*;

pub mod validation;
pub mod optimizer;
pub mod lod;
pub mod subdivision;

pub use optimizer::MeshOptimizer;
pub use validation::{MeshValidator, ValidationReport};
pub use lod::LodGenerator;

/// Clean mesh by removing degenerate triangles, duplicate vertices, etc.
pub fn clean_mesh(mesh: &mut Mesh) -> Result<()> {
    remove_degenerate_triangles(mesh)?;
    remove_duplicate_vertices(mesh)?;
    mesh.compute_normals();
    Ok(())
}

/// Remove degenerate triangles (zero area, invalid indices)
fn remove_degenerate_triangles(mesh: &mut Mesh) -> Result<()> {
    let mut valid_indices = Vec::new();
    let epsilon = 1e-6;

    for chunk in mesh.indices.chunks(3) {
        if chunk.len() != 3 {
            continue;
        }

        let i0 = chunk[0] as usize;
        let i1 = chunk[1] as usize;
        let i2 = chunk[2] as usize;

        if i0 >= mesh.vertices.len() || i1 >= mesh.vertices.len() || i2 >= mesh.vertices.len() {
            continue;
        }

        let v0 = mesh.vertices[i0];
        let v1 = mesh.vertices[i1];
        let v2 = mesh.vertices[i2];

        let edge1 = v1 - v0;
        let edge2 = v2 - v0;
        let area = edge1.cross(&edge2).magnitude() * 0.5;

        if area > epsilon {
            valid_indices.extend_from_slice(chunk);
        }
    }

    mesh.indices = valid_indices;
    Ok(())
}

/// Remove duplicate vertices
fn remove_duplicate_vertices(mesh: &mut Mesh) -> Result<()> {
    // Simple implementation - can be optimized with spatial hashing
    let mut new_vertices = Vec::new();
    let mut index_map: Vec<u32> = Vec::new();
    let epsilon = 1e-6;

    for vertex in &mesh.vertices {
        let mut found = None;

        for (i, &vertex) in mesh.vertices.iter().enumerate() {
            if (vertex.coords - vertex.coords).norm() < epsilon {
                found = Some(i as u32);
                break;
            }
        }

        match found {
            Some(idx) => index_map.push(idx),
            None => {
                new_vertices.push(*vertex);
                index_map.push((new_vertices.len() - 1) as u32);
            }
        }
    }

    // Remap indices
    for index in &mut mesh.indices {
        if (*index as usize) < index_map.len() {
            *index = index_map[*index as usize];
        }
    }

    mesh.vertices = new_vertices;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_clean_mesh() {
        let mut mesh = Mesh::new();
        // Add some test data
        mesh.vertices.push(nalgebra::Point3::new(0.0, 0.0, 0.0));
        mesh.vertices.push(nalgebra::Point3::new(1.0, 0.0, 0.0));
        mesh.vertices.push(nalgebra::Point3::new(0.0, 1.0, 0.0));
        mesh.indices.extend_from_slice(&[0, 1, 2]);

        clean_mesh(&mut mesh).unwrap();
        assert!(mesh.vertex_count() > 0);
    }
}
pub mod advanced_optimizer;
pub use advanced_optimizer::AdvancedOptimizer;
