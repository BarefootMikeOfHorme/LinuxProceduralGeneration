//! Engine-Specific Export Formats
//!
//! Professional export with engine-specific optimizations:
//! - Unity (FBX, coordinate transform, scale)
//! - Unreal Engine (FBX, coordinate transform, materials)
//! - CryEngine (CGF, coordinate transform)
//! - Lumix Engine (homage to our roots)
//! - glTF 2.0 (universal PBR format)

use crate::geometry::Mesh;
use crate::{Result, GeometryError};
use nalgebra::{Matrix4, Point3, Vector3};
use std::path::Path;
use std::fs::File;
use std::io::Write;

/// Engine-specific coordinate system transforms
#[derive(Debug, Clone, Copy)]
pub enum Engine {
    /// Unity: Y-up, left-handed, scale 1.0
    Unity,
    /// Unreal: Z-up, left-handed, scale 100.0 (cm)
    Unreal,
    /// CryEngine: Z-up, right-handed, scale 100.0 (cm)
    CryEngine,
    /// Lumix Engine: Y-up, right-handed, scale 1.0
    Lumix,
    /// Godot: Y-up, right-handed, scale 1.0
    Godot,
    /// Generic: No transform
    Generic,
}

impl Engine {
    /// Get coordinate transform matrix for this engine
    pub fn transform_matrix(&self) -> Matrix4<f32> {
        match self {
            Engine::Unity => {
                // Y-up, left-handed (flip Z)
                Matrix4::new(
                    1.0, 0.0, 0.0, 0.0,
                    0.0, 1.0, 0.0, 0.0,
                    0.0, 0.0, -1.0, 0.0,
                    0.0, 0.0, 0.0, 1.0,
                )
            }
            Engine::Unreal => {
                // Z-up, left-handed, scale 100 (meters to cm)
                Matrix4::new(
                    100.0, 0.0, 0.0, 0.0,
                    0.0, 0.0, 100.0, 0.0,
                    0.0, 100.0, 0.0, 0.0,
                    0.0, 0.0, 0.0, 1.0,
                )
            }
            Engine::CryEngine => {
                // Z-up, right-handed, scale 100
                Matrix4::new(
                    100.0, 0.0, 0.0, 0.0,
                    0.0, 0.0, 100.0, 0.0,
                    0.0, -100.0, 0.0, 0.0,
                    0.0, 0.0, 0.0, 1.0,
                )
            }
            Engine::Lumix => {
                // Y-up, right-handed (native)
                Matrix4::identity()
            }
            Engine::Godot => Matrix4::identity(),
            Engine::Generic => Matrix4::identity(),
        }
    }

    /// Get recommended export format
    pub fn recommended_format(&self) -> &'static str {
        match self {
            Engine::Unity => "fbx",
            Engine::Unreal => "fbx",
            Engine::CryEngine => "obj", // CryEngine prefers OBJ for import
            Engine::Lumix => "obj",
            Engine::Godot => "obj",
            Engine::Generic => "gltf",
        }
    }

    /// Get engine-specific metadata
    pub fn metadata(&self) -> EngineMetadata {
        match self {
            Engine::Unity => EngineMetadata {
                name: "Unity",
                coordinate_system: "Y-up, Left-handed",
                scale_factor: 1.0,
                unit: "meters",
                notes: "Unity uses left-handed coordinates with Y-up",
            },
            Engine::Unreal => EngineMetadata {
                name: "Unreal Engine",
                coordinate_system: "Z-up, Left-handed",
                scale_factor: 100.0,
                unit: "centimeters",
                notes: "Unreal uses cm as base unit (100x meters)",
            },
            Engine::CryEngine => EngineMetadata {
                name: "CryEngine",
                coordinate_system: "Z-up, Right-handed",
                scale_factor: 100.0,
                unit: "centimeters",
                notes: "CryEngine uses right-handed Z-up coordinates",
            },
            Engine::Lumix => EngineMetadata {
                name: "Lumix Engine",
                coordinate_system: "Y-up, Right-handed",
                scale_factor: 1.0,
                unit: "meters",
                notes: "Lumix: lightweight, open-source engine (homage)",
            },
            Engine::Godot => EngineMetadata {
                name: "Godot",
                coordinate_system: "Y-up, Right-handed",
                scale_factor: 1.0,
                unit: "meters",
                notes: "Godot OBJ export uses the native Y-up coordinate system",
            },
            Engine::Generic => EngineMetadata {
                name: "Generic",
                coordinate_system: "Y-up, Right-handed",
                scale_factor: 1.0,
                unit: "meters",
                notes: "Standard OpenGL/glTF coordinates",
            },
        }
    }
}

#[derive(Debug, Clone)]
pub struct EngineMetadata {
    pub name: &'static str,
    pub coordinate_system: &'static str,
    pub scale_factor: f32,
    pub unit: &'static str,
    pub notes: &'static str,
}

/// Export mesh for specific engine
pub fn export_for_engine(
    mesh: &Mesh,
    path: &Path,
    engine: Engine,
) -> Result<()> {
    // Transform mesh for engine coordinate system
    let mut transformed = mesh.clone();
    let transform = engine.transform_matrix();
    transformed.transform(&transform);

    // Only OBJ is currently implemented. The requested extension is part of
    // the contract: never write OBJ bytes under an FBX/glTF filename.
    let extension = path
        .extension()
        .and_then(|value| value.to_str())
        .unwrap_or_default()
        .to_ascii_lowercase();
    let metadata = engine.metadata();

    match extension.as_str() {
        "obj" => export_obj_for_engine(&transformed, path, &metadata),
        "fbx" => export_fbx_for_engine(&transformed, path, &metadata),
        "gltf" | "glb" => export_gltf_for_engine(&transformed, path, &metadata),
        _ => Err(GeometryError::ExportError(format!(
            "Unsupported engine export extension '.{extension}'; use .obj"
        ))),
    }
}

/// Reject FBX requests until a real FBX serializer is implemented.
fn export_fbx_for_engine(
    _mesh: &Mesh,
    _path: &Path,
    metadata: &EngineMetadata,
) -> Result<()> {
    Err(GeometryError::ExportError(format!(
        "FBX export for {} is not implemented; use OBJ or a future validated FBX serializer",
        metadata.name
    )))
}

/// Export OBJ with engine-specific comments
fn export_obj_for_engine(
    mesh: &Mesh,
    path: &Path,
    metadata: &EngineMetadata,
) -> Result<()> {
    let mut file = File::create(path)
        .map_err(|e| GeometryError::ExportError(format!("Failed to create OBJ: {}", e)))?;

    writeln!(file, "# VaultMind Forge - {}", metadata.name).ok();
    writeln!(file, "# Coordinate System: {}", metadata.coordinate_system).ok();
    writeln!(file, "# Unit: {}", metadata.unit).ok();
    writeln!(file, "# {}", metadata.notes).ok();
    writeln!(file, "").ok();

    export_obj_data(&mut file, mesh)?;

    Ok(())
}

/// Reject glTF requests until a complete glTF serializer is implemented.
fn export_gltf_for_engine(
    _mesh: &Mesh,
    _path: &Path,
    metadata: &EngineMetadata,
) -> Result<()> {
    Err(GeometryError::ExportError(format!(
        "glTF export for {} is not implemented; use OBJ or a future validated glTF serializer",
        metadata.name
    )))
}

/// Write OBJ mesh data
fn export_obj_data(file: &mut File, mesh: &Mesh) -> Result<()> {
    // Vertices
    for v in &mesh.vertices {
        writeln!(file, "v {} {} {}", v.x, v.y, v.z).ok();
    }

    // Normals
    for n in &mesh.normals {
        writeln!(file, "vn {} {} {}", n.x, n.y, n.z).ok();
    }

    // UVs
    for uv in &mesh.uvs {
        writeln!(file, "vt {} {}", uv.0, uv.1).ok();
    }

    // Faces. Only reference UV/normal indices when the mesh actually
    // contains those attributes.
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
            writeln!(file, "f {} {} {}", refs[0], refs[1], refs[2]).ok();
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::geometry::primitives::Box;
    use crate::geometry::Primitive;

    #[test]
    fn test_engine_transforms() {
        let unity = Engine::Unity.transform_matrix();
        let unreal = Engine::Unreal.transform_matrix();
        let cryengine = Engine::CryEngine.transform_matrix();

        assert_ne!(unity, unreal);
        assert_ne!(unreal, cryengine);
    }

    #[test]
    fn test_engine_metadata() {
        let meta = Engine::Unreal.metadata();
        assert_eq!(meta.scale_factor, 100.0);
        assert_eq!(meta.unit, "centimeters");
    }

    #[test]
    fn test_lumix_homage() {
        let meta = Engine::Lumix.metadata();
        assert!(meta.notes.contains("homage"));
        assert_eq!(meta.scale_factor, 1.0);
    }
}
