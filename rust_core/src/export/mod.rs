//! Multi-format mesh export
//!
//! Export geometry to various formats optimized for different game engines:
//! - OBJ (universal)
//! - FBX (Unity, Unreal, Blender)
//! - glTF (web, modern engines)
//! - Engine-specific formats

use crate::geometry::Mesh;
use crate::{Result, GeometryError};
use std::fs::File;
use std::io::Write;
use std::path::Path;

/// Supported export formats
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ExportFormat {
    Obj,
    Fbx,
    Gltf,
    Unity,
    Godot,
    Unreal,
}

/// Target engine for optimization
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TargetEngine {
    Universal,
    Unity,
    Godot,
    Unreal,
    Custom,
}

/// Export mesh to file
pub fn export(mesh: &Mesh, path: &Path, format: ExportFormat) -> Result<()> {
    match format {
        ExportFormat::Obj => export_obj(mesh, path),
        ExportFormat::Fbx => export_fbx(mesh, path),
        ExportFormat::Gltf => export_gltf(mesh, path),
        ExportFormat::Unity => export_unity(mesh, path),
        ExportFormat::Godot => export_godot(mesh, path),
        ExportFormat::Unreal => export_unreal(mesh, path),
    }
}

/// Export to OBJ format
fn export_obj(mesh: &Mesh, path: &Path) -> Result<()> {
    let mut file = File::create(path)?;

    // Write header
    writeln!(file, "# VaultMind Forge - Exported OBJ")?;
    writeln!(file, "# Vertices: {}", mesh.vertices.len())?;
    writeln!(file, "# Triangles: {}", mesh.indices.len() / 3)?;
    writeln!(file)?;

    // Write vertices
    for v in &mesh.vertices {
        writeln!(file, "v {} {} {}", v.x, v.y, v.z)?;
    }

    // Write normals
    for n in &mesh.normals {
        writeln!(file, "vn {} {} {}", n.x, n.y, n.z)?;
    }

    // Write UVs
    for &(u, v) in &mesh.uvs {
        writeln!(file, "vt {} {}", u, v)?;
    }

    // Write faces (OBJ indices are 1-based)
    for chunk in mesh.indices.chunks(3) {
        if chunk.len() == 3 {
            writeln!(
                file,
                "f {}/{}/{} {}/{}/{} {}/{}/{}",
                chunk[0] + 1, chunk[0] + 1, chunk[0] + 1,
                chunk[1] + 1, chunk[1] + 1, chunk[1] + 1,
                chunk[2] + 1, chunk[2] + 1, chunk[2] + 1
            )?;
        }
    }

    Ok(())
}

/// Export to FBX format (placeholder)
fn export_fbx(mesh: &Mesh, path: &Path) -> Result<()> {
    // FBX export requires a complex binary or ASCII format
    // For now, export as OBJ with .fbx extension as placeholder
    export_obj(mesh, path)
}

/// Export to glTF format (placeholder)
fn export_gltf(mesh: &Mesh, path: &Path) -> Result<()> {
    // glTF is a JSON-based format with binary buffer
    // TODO: Implement proper glTF export
    Err(GeometryError::ExportError("glTF export not yet implemented".to_string()))
}

/// Export optimized for Unity
fn export_unity(mesh: &Mesh, path: &Path) -> Result<()> {
    // Unity prefers FBX
    // Apply Unity-specific optimizations:
    // - Y-up coordinate system
    // - Right-handed coordinates
    export_fbx(mesh, path)
}

/// Export optimized for Godot
fn export_godot(mesh: &Mesh, path: &Path) -> Result<()> {
    // Godot supports OBJ, glTF
    // Y-up, right-handed
    export_obj(mesh, path)
}

/// Export optimized for Unreal
fn export_unreal(mesh: &Mesh, path: &Path) -> Result<()> {
    // Unreal prefers FBX
    // Z-up coordinate system
    // TODO: Apply coordinate system transformation
    export_fbx(mesh, path)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::geometry::primitives::Box;
    use crate::geometry::Primitive;
    use nalgebra::Vector3;
    use std::path::PathBuf;

    #[test]
    fn test_obj_export() {
        let b = Box::new(Vector3::new(2.0, 2.0, 2.0));
        let mesh = b.to_mesh().unwrap();

        let path = PathBuf::from("test_output.obj");
        export_obj(&mesh, &path).unwrap();

        // Cleanup
        std::fs::remove_file(path).ok();
    }
}
pub mod engine_formats;
pub use engine_formats::*;
