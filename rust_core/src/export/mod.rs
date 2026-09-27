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

/// Default auto-smooth angle for export, in degrees.
///
/// 30 is Blender's "Smooth by Angle" default. It matters that this is not 180:
/// most meshes reaching an exporter are unmarked, including CSG results, and at
/// 180 every unmarked crease would smooth away and a boolean-cut box would
/// arrive as a rounded blob. At 30 a marked edge still wins outright, a
/// tessellated curve stays smooth, and a hard unmarked edge stays hard.
pub const DEFAULT_EXPORT_SMOOTH_ANGLE_DEG: f32 = 30.0;

/// Format a float for OBJ output, collapsing negative zero to `0`.
///
/// Cross products produce `-0.0` readily, and writing it makes the same normal
/// direction appear in two spellings: `vn 0 0 1` and `vn 0 -0 1`. Every OBJ
/// parser reads both as the same number, but any consumer comparing or hashing
/// the text sees six distinct face normals on a cube instead of six distinct
/// faces, and diffing an export is needlessly noisy.
pub(crate) fn obj_float(value: f32) -> String {
    let v = if value == 0.0 { 0.0 } else { value };
    format!("{v}")
}

/// Export to OBJ format
fn export_obj(mesh: &Mesh, path: &Path) -> Result<()> {
    export_obj_with_smoothing(mesh, path, DEFAULT_EXPORT_SMOOTH_ANGLE_DEG)
}

/// Export to OBJ, deriving the render form at a given auto-smooth angle.
///
/// The render form is derived rather than the welded mesh written directly,
/// because OBJ indexes position, UV, and normal independently and this writer
/// keeps all three 1:1. That only works if every output vertex has exactly one
/// normal and one UV, which is false for any mesh with a crease or a UV seam. A
/// welded box has eight vertices shared by three faces each and therefore cannot
/// carry a per-face UV at all, so writing it 1:1 emitted eight copies of
/// `vt 0 0`. Splitting first is what makes the UVs real.
fn export_obj_with_smoothing(mesh: &Mesh, path: &Path, smooth_angle_deg: f32) -> Result<()> {
    let render = mesh.split_for_render(smooth_angle_deg);
    let mut file = File::create(path)?;

    // Write header
    writeln!(file, "# VaultMind Forge - Exported OBJ")?;
    writeln!(file, "# Source vertices: {}", mesh.vertices.len())?;
    writeln!(file, "# Render vertices: {}", render.vertices.len())?;
    writeln!(file, "# Triangles: {}", render.indices.len() / 3)?;
    writeln!(file, "# Auto-smooth angle: {smooth_angle_deg}")?;
    writeln!(file, "# Marked sharp edges: {}", mesh.sharp_edges.len())?;
    writeln!(file)?;

    // Write vertices
    for v in &render.vertices {
        writeln!(
            file,
            "v {} {} {}",
            obj_float(v.x),
            obj_float(v.y),
            obj_float(v.z)
        )?;
    }

    // Write normals
    for n in &render.normals {
        writeln!(
            file,
            "vn {} {} {}",
            obj_float(n.x),
            obj_float(n.y),
            obj_float(n.z)
        )?;
    }

    // Write UVs
    for &(u, v) in &render.uvs {
        writeln!(file, "vt {} {}", obj_float(u), obj_float(v))?;
    }

    // Faces. The split guarantees one normal and one UV per vertex, so all
    // three index streams line up and the reference is unambiguous.
    let has_uvs = render.uvs.len() == render.vertices.len();
    let has_normals = render.normals.len() == render.vertices.len();

    for chunk in render.indices.chunks(3) {
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

        // Topology survives the round trip untouched: the split duplicates
        // vertices, it never adds or removes a triangle.
        assert_eq!(reloaded.triangle_count(), mesh.triangle_count());

        // The vertex count is the render form's, not the welded form's. A cube's
        // eight welded vertices become 36, not the 24 a quad-based mesh would
        // give: `Mesh` is triangles-only and carries no polygon identity, so each
        // of the 12 triangles pins its own three corners and the two triangles
        // of a face cannot discover that they share two. The result is larger
        // than necessary but lossless, and every corner still carries the right
        // normal and UV.
        let render = mesh.split_for_render(DEFAULT_EXPORT_SMOOTH_ANGLE_DEG);
        assert_eq!(reloaded.vertex_count(), render.vertex_count());
        assert_eq!(reloaded.vertex_count(), 36);
        assert_eq!(render.unique_position_count(), 8, "positions stay welded");

        // Cleanup
        std::fs::remove_file(path).ok();
    }

    #[test]
    fn test_obj_export_carries_real_uvs() {
        // The defect this guards: a welded box has eight vertices shared by three
        // faces each, so it cannot hold a per-face UV. Writing it 1:1 emitted
        // eight copies of `vt 0 0` and the exported box was untexturable.
        let mesh = Box::new(Vector3::new(2.0, 2.0, 2.0)).to_mesh().unwrap();
        assert!(
            mesh.uvs.iter().all(|&(u, v)| u == 0.0 && v == 0.0),
            "a box has no meaningful single-UV-per-vertex parameterisation, so this \
             test would not be testing anything if the topology UVs were real"
        );

        let path = PathBuf::from("test_output_uvs.obj");
        export_obj(&mesh, &path).unwrap();
        let text = std::fs::read_to_string(&path).unwrap();

        let render = mesh.split_for_render(DEFAULT_EXPORT_SMOOTH_ANGLE_DEG);
        let vt_lines: Vec<&str> = text.lines().filter(|l| l.starts_with("vt ")).collect();
        assert_eq!(
            vt_lines.len(),
            render.vertices.len(),
            "expected one vt per render vertex"
        );

        // A planar box mapping puts the four corners of each face's 0..1 square
        // at (0,0), (1,0), (1,1), and (0,1). All four must appear: the old export
        // emitted only `vt 0 0`, which is what made the cube untexturable.
        let distinct: std::collections::HashSet<&str> = vt_lines.iter().copied().collect();
        for corner in ["vt 0 0", "vt 1 0", "vt 1 1", "vt 0 1"] {
            assert!(
                distinct.contains(corner),
                "the export is missing {corner}; found {distinct:?}"
            );
        }

        // Negative zero must not reach the file: it would spell one normal
        // direction two ways.
        assert!(
            !text.contains("-0\n") && !text.contains(" -0 "),
            "the export contains negative zero"
        );

        // Every face must reference position, UV, and normal.
        let faces = text.lines().filter(|l| l.starts_with("f ")).count();
        assert_eq!(faces, 12);
        for line in text.lines().filter(|l| l.starts_with("f ")) {
            for reference in line[2..].split_whitespace() {
                assert_eq!(
                    reference.split('/').count(),
                    3,
                    "face reference {reference} is missing a UV or normal index"
                );
            }
        }

        std::fs::remove_file(path).ok();
    }

    #[test]
    fn test_obj_export_preserves_marked_creases() {
        // A box marks all twelve edges sharp, so at any auto-smooth angle it must
        // export as six flat faces rather than one smoothed blob.
        let mesh = Box::new(Vector3::new(2.0, 2.0, 2.0)).to_mesh().unwrap();
        let path = PathBuf::from("test_output_crease.obj");
        export_obj(&mesh, &path).unwrap();
        let text = std::fs::read_to_string(&path).unwrap();

        let vn: Vec<&str> = text.lines().filter(|l| l.starts_with("vn ")).collect();
        // 36 render vertices, but a cube has only 6 face planes, so there must be
        // exactly 6 distinct normals. This is also what catches negative zero:
        // `vn 0 -0 1` and `vn 0 0 1` are the same direction spelled two ways and
        // would read as 7.
        let distinct: std::collections::HashSet<&str> = vn.iter().copied().collect();
        assert_eq!(
            distinct.len(),
            6,
            "a cube should export exactly 6 distinct face normals, found {}",
            distinct.len()
        );

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

