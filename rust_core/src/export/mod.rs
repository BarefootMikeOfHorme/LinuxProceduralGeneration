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

    // Write faces (OBJ indices are 1-based). Only reference UV/normal
    // indices when the mesh actually contains those attributes.
    let has_uvs = mesh.uvs.len() >= mesh.vertices.len();
    let has_normals = mesh.normals.len() >= mesh.vertices.len();

    for chunk in mesh.indices.chunks(3) {
        if chunk.len() == 3 {
            let refs: Vec<String> = chunk
                .iter()
                .map(|index| {
                    let vertex = index + 1;
                    match (has_uvs, has_normals) {
                        (true, true) => format!("{vertex}/{vertex}/{vertex}"),
                        (false, true) => format!("{vertex}//{vertex}"),
                        (true, false) => format!("{vertex}/{vertex}"),
                        (false, false) => format!("{vertex}"),
                    }
                })
                .collect();
            writeln!(file, "f {} {} {}", refs[0], refs[1], refs[2])?;
        }
    }

    Ok(())
}

/// Reject FBX export until a real serializer is implemented.
fn export_fbx(_mesh: &Mesh, _path: &Path) -> Result<()> {
    Err(GeometryError::ExportError(
        "FBX export is not implemented; use OBJ or a future validated FBX serializer".to_string(),
    ))
}

/// Export to glTF format (placeholder)
fn export_gltf(mesh: &Mesh, path: &Path) -> Result<()> {
    // glTF is a JSON-based format with binary buffer
    // TODO: Implement proper glTF export
    Err(GeometryError::ExportError("glTF export not yet implemented".to_string()))
}

/// Export optimized for Unity. OBJ is the only validated engine format.
fn export_unity(mesh: &Mesh, path: &Path) -> Result<()> {
    engine_formats::export_for_engine(mesh, path, engine_formats::Engine::Unity)
}

/// Export optimized for Godot using validated OBJ output.
fn export_godot(mesh: &Mesh, path: &Path) -> Result<()> {
    engine_formats::export_for_engine(mesh, path, engine_formats::Engine::Godot)
}

/// Export optimized for Unreal. OBJ is the only validated engine format.
fn export_unreal(mesh: &Mesh, path: &Path) -> Result<()> {
    engine_formats::export_for_engine(mesh, path, engine_formats::Engine::Unreal)
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
        let reloaded = crate::mesh::obj::load_obj(&path).unwrap();
        assert_eq!(reloaded.vertex_count(), mesh.vertex_count());
        assert_eq!(reloaded.triangle_count(), mesh.triangle_count());

        // Cleanup
        std::fs::remove_file(path).ok();
    }

    #[test]
    fn test_unsupported_formats_fail_without_creating_files() {
        let b = Box::new(Vector3::new(2.0, 2.0, 2.0));
        let mesh = b.to_mesh().unwrap();
        let base = std::env::temp_dir().join(format!("lpg-export-{}", std::process::id()));

        let fbx_path = base.with_extension("fbx");
        assert!(export_fbx(&mesh, &fbx_path).is_err());
        assert!(!fbx_path.exists());

        let gltf_path = base.with_extension("gltf");
        assert!(export_gltf(&mesh, &gltf_path).is_err());
        assert!(!gltf_path.exists());

        let obj_path = base.with_extension("obj");
        assert!(export_unity(&mesh, &obj_path).is_ok());
        assert!(obj_path.exists());
        std::fs::remove_file(obj_path).ok();
    }
}
pub mod engine_formats;
pub use engine_formats::*;
