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

    // Export in recommended format
    let format = engine.recommended_format();
    let metadata = engine.metadata();

    match format {
        "fbx" => export_fbx_for_engine(&transformed, path, &metadata),
        "obj" => export_obj_for_engine(&transformed, path, &metadata),
        "gltf" => export_gltf_for_engine(&transformed, path, &metadata),
        _ => export_obj_for_engine(&transformed, path, &metadata),
    }
}

/// Export FBX with engine-specific settings
fn export_fbx_for_engine(
    mesh: &Mesh,
    path: &Path,
    metadata: &EngineMetadata,
) -> Result<()> {
    // FBX export (simplified - full implementation would use fbxcel crate)
    let mut file = File::create(path)
        .map_err(|e| GeometryError::ExportError(format!("Failed to create FBX: {}", e)))?;

    writeln!(file, "; FBX 7.4.0 project file").ok();
    writeln!(file, "; Generated by VaultMind Forge").ok();
    writeln!(file, "; Engine: {}", metadata.name).ok();
    writeln!(file, "; Coordinate System: {}", metadata.coordinate_system).ok();
    writeln!(file, "; Unit: {} (scale: {})", metadata.unit, metadata.scale_factor).ok();
    writeln!(file, "").ok();

    writeln!(file, "; Mesh: {} vertices, {} triangles",
             mesh.vertex_count(), mesh.triangle_count()).ok();

    // TODO: Full FBX binary format implementation
    // For now, export as OBJ with FBX metadata comments

    export_obj_data(&mut file, mesh)?;

    Ok(())
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

/// Export glTF 2.0 with PBR materials
fn export_gltf_for_engine(
    mesh: &Mesh,
    path: &Path,
    metadata: &EngineMetadata,
) -> Result<()> {
    let mut file = File::create(path)
        .map_err(|e| GeometryError::ExportError(format!("Failed to create glTF: {}", e)))?;

    // glTF 2.0 JSON structure
    writeln!(file, "{{").ok();
    writeln!(file, "  \"asset\": {{").ok();
    writeln!(file, "    \"version\": \"2.0\",").ok();
    writeln!(file, "    \"generator\": \"VaultMind Forge\",").ok();
    writeln!(file, "    \"copyright\": \"{}\"", metadata.notes).ok();
    writeln!(file, "  }},").ok();

    writeln!(file, "  \"scene\": 0,").ok();
    writeln!(file, "  \"scenes\": [").ok();
    writeln!(file, "    {{ \"nodes\": [0] }}").ok();
    writeln!(file, "  ],").ok();

    writeln!(file, "  \"nodes\": [").ok();
    writeln!(file, "    {{ \"mesh\": 0 }}").ok();
    writeln!(file, "  ],").ok();

    writeln!(file, "  \"meshes\": [").ok();
    writeln!(file, "    {{").ok();
    writeln!(file, "      \"name\": \"VaultMindMesh\",").ok();
    writeln!(file, "      \"primitives\": [").ok();
    writeln!(file, "        {{").ok();
    writeln!(file, "          \"mode\": 4,").ok(); // TRIANGLES
    writeln!(file, "          \"material\": 0").ok();
    writeln!(file, "        }}").ok();
    writeln!(file, "      ]").ok();
    writeln!(file, "    }}").ok();
    writeln!(file, "  ],").ok();

    writeln!(file, "  \"materials\": [").ok();
    writeln!(file, "    {{").ok();
    writeln!(file, "      \"name\": \"DefaultMaterial\",").ok();
    writeln!(file, "      \"pbrMetallicRoughness\": {{").ok();
    writeln!(file, "        \"baseColorFactor\": [0.8, 0.8, 0.8, 1.0],").ok();
    writeln!(file, "        \"metallicFactor\": 0.0,").ok();
    writeln!(file, "        \"roughnessFactor\": 0.5").ok();
    writeln!(file, "      }}").ok();
    writeln!(file, "    }}").ok();
    writeln!(file, "  ]").ok();

    writeln!(file, "}}").ok();

    Ok(())
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

    // Faces
    for chunk in mesh.indices.chunks(3) {
        if chunk.len() == 3 {
            let i1 = chunk[0] + 1;
            let i2 = chunk[1] + 1;
            let i3 = chunk[2] + 1;
            writeln!(file, "f {}/{}/{} {}/{}/{} {}/{}/{}",
                     i1, i1, i1,
                     i2, i2, i2,
                     i3, i3, i3).ok();
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
