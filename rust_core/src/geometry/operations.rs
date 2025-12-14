//! Procedural geometry operations (extrude, revolve, loft, sweep)

use nalgebra::{Point3, Vector3};
use crate::geometry::Mesh;
use crate::{Result, GeometryError};

/// Extrude a 2D profile along a direction
///
/// # Arguments
/// * `profile` - 2D points forming the profile to extrude
/// * `direction` - Extrusion direction vector
/// * `distance` - Extrusion distance
///
/// # Returns
/// Extruded 3D mesh
pub fn extrude(
    profile: &[(f32, f32)],
    direction: Vector3<f32>,
    distance: f32,
) -> Result<Mesh> {
    if profile.len() < 3 {
        return Err(GeometryError::InvalidParameters(
            "Profile must have at least 3 points".to_string(),
        ));
    }

    let mut mesh = Mesh::new();
    let dir = direction.normalize() * distance;

    // Create bottom and top profiles
    for &(x, y) in profile {
        // Bottom vertex
        mesh.vertices.push(Point3::new(x, y, 0.0));
        // Top vertex
        mesh.vertices.push(Point3::new(x + dir.x, y + dir.y, dir.z));
    }

    // Generate side faces
    let n = profile.len();
    for i in 0..n {
        let curr_bottom = (i * 2) as u32;
        let curr_top = curr_bottom + 1;
        let next_bottom = (((i + 1) % n) * 2) as u32;
        let next_top = next_bottom + 1;

        // Two triangles per quad
        mesh.indices.push(curr_bottom);
        mesh.indices.push(next_bottom);
        mesh.indices.push(curr_top);

        mesh.indices.push(curr_top);
        mesh.indices.push(next_bottom);
        mesh.indices.push(next_top);
    }

    mesh.compute_normals();
    mesh.uvs = vec![(0.0, 0.0); mesh.vertices.len()];

    Ok(mesh)
}

/// Revolve a 2D profile around an axis
///
/// # Arguments
/// * `profile` - 2D points forming the profile to revolve
/// * `axis` - Axis of revolution
/// * `angle` - Revolution angle in radians (2π for full circle)
/// * `segments` - Number of segments around the axis
///
/// # Returns
/// Revolved 3D mesh
pub fn revolve(
    profile: &[(f32, f32)],
    axis: Vector3<f32>,
    angle: f32,
    segments: u32,
) -> Result<Mesh> {
    if profile.len() < 2 {
        return Err(GeometryError::InvalidParameters(
            "Profile must have at least 2 points".to_string(),
        ));
    }

    if segments < 3 {
        return Err(GeometryError::InvalidParameters(
            "Must have at least 3 segments".to_string(),
        ));
    }

    let mut mesh = Mesh::new();

    // Generate vertices by rotating profile around axis
    for seg in 0..=segments {
        let theta = angle * seg as f32 / segments as f32;
        let cos_theta = theta.cos();
        let sin_theta = theta.sin();

        for &(x, y) in profile {
            // Simple rotation around Y axis (can be generalized)
            let px = x * cos_theta;
            let py = y;
            let pz = x * sin_theta;

            mesh.vertices.push(Point3::new(px, py, pz));
        }
    }

    // Generate indices
    let profile_len = profile.len();
    for seg in 0..segments {
        for i in 0..(profile_len - 1) {
            let curr = (seg * profile_len as u32 + i as u32) as u32;
            let next = ((seg + 1) * profile_len as u32 + i as u32) as u32;

            mesh.indices.push(curr);
            mesh.indices.push(next);
            mesh.indices.push(curr + 1);

            mesh.indices.push(curr + 1);
            mesh.indices.push(next);
            mesh.indices.push(next + 1);
        }
    }

    mesh.compute_normals();
    mesh.uvs = vec![(0.0, 0.0); mesh.vertices.len()];

    Ok(mesh)
}

/// Loft between multiple cross-sections
///
/// # Arguments
/// * `sections` - Array of cross-section profiles
/// * `closed` - Whether to close the loft back to the first section
///
/// # Returns
/// Lofted 3D mesh
pub fn loft(sections: &[Vec<(f32, f32, f32)>], closed: bool) -> Result<Mesh> {
    if sections.len() < 2 {
        return Err(GeometryError::InvalidParameters(
            "Need at least 2 cross-sections for lofting".to_string(),
        ));
    }

    // Verify all sections have the same number of points
    let section_len = sections[0].len();
    if !sections.iter().all(|s| s.len() == section_len) {
        return Err(GeometryError::InvalidParameters(
            "All cross-sections must have the same number of points".to_string(),
        ));
    }

    let mut mesh = Mesh::new();

    // Add all section vertices
    for section in sections {
        for &(x, y, z) in section {
            mesh.vertices.push(Point3::new(x, y, z));
        }
    }

    // Generate faces between sections
    let num_sections = sections.len();
    let section_count = if closed { num_sections } else { num_sections - 1 };

    for sec in 0..section_count {
        let next_sec = (sec + 1) % num_sections;

        for i in 0..section_len {
            let next_i = (i + 1) % section_len;

            let curr = (sec * section_len + i) as u32;
            let curr_next = (sec * section_len + next_i) as u32;
            let next = (next_sec * section_len + i) as u32;
            let next_next = (next_sec * section_len + next_i) as u32;

            mesh.indices.push(curr);
            mesh.indices.push(next);
            mesh.indices.push(curr_next);

            mesh.indices.push(curr_next);
            mesh.indices.push(next);
            mesh.indices.push(next_next);
        }
    }

    mesh.compute_normals();
    mesh.uvs = vec![(0.0, 0.0); mesh.vertices.len()];

    Ok(mesh)
}

/// Sweep a profile along a path
///
/// # Arguments
/// * `profile` - 2D profile to sweep
/// * `path` - 3D path curve
/// * `closed` - Whether the sweep is closed
///
/// # Returns
/// Swept 3D mesh
pub fn sweep(
    profile: &[(f32, f32)],
    path: &[Point3<f32>],
    closed: bool,
) -> Result<Mesh> {
    if profile.len() < 3 {
        return Err(GeometryError::InvalidParameters(
            "Profile must have at least 3 points".to_string(),
        ));
    }

    if path.len() < 2 {
        return Err(GeometryError::InvalidParameters(
            "Path must have at least 2 points".to_string(),
        ));
    }

    let mut mesh = Mesh::new();

    // For each point on the path, create a cross-section
    // This is a simplified implementation - a full implementation would
    // compute proper tangents and normals along the path
    for path_point in path {
        for &(x, y) in profile {
            mesh.vertices.push(Point3::new(
                path_point.x + x,
                path_point.y + y,
                path_point.z,
            ));
        }
    }

    // Generate faces
    let profile_len = profile.len();
    let path_count = if closed { path.len() } else { path.len() - 1 };

    for p in 0..path_count {
        let next_p = (p + 1) % path.len();

        for i in 0..profile_len {
            let next_i = (i + 1) % profile_len;

            let curr = (p * profile_len + i) as u32;
            let curr_next = (p * profile_len + next_i) as u32;
            let next = (next_p * profile_len + i) as u32;
            let next_next = (next_p * profile_len + next_i) as u32;

            mesh.indices.push(curr);
            mesh.indices.push(next);
            mesh.indices.push(curr_next);

            mesh.indices.push(curr_next);
            mesh.indices.push(next);
            mesh.indices.push(next_next);
        }
    }

    mesh.compute_normals();
    mesh.uvs = vec![(0.0, 0.0); mesh.vertices.len()];

    Ok(mesh)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extrude() {
        let profile = vec![(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)];
        let mesh = extrude(&profile, Vector3::z(), 2.0).unwrap();
        assert!(mesh.vertex_count() > 0);
    }

    #[test]
    fn test_revolve() {
        let profile = vec![(0.5, 0.0), (1.0, 0.5), (0.5, 1.0)];
        let mesh = revolve(&profile, Vector3::y(), 2.0 * std::f32::consts::PI, 32).unwrap();
        assert!(mesh.vertex_count() > 0);
    }
}
