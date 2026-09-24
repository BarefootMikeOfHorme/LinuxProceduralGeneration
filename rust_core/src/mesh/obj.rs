//! Minimal, validated OBJ mesh loading.
//!
//! This loader supports the geometry subset needed by LPG's mesh workflows:
//! vertices, UVs, normals, polygon faces, and positive/negative OBJ indices.
//! It intentionally does not claim to preserve OBJ materials, groups,
//! smoothing groups, or scene semantics.

use crate::geometry::Mesh;
use crate::{GeometryError, Result};
use nalgebra::{Point3, Vector3};
use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;

type CornerKey = (usize, Option<usize>, Option<usize>);

fn obj_error(message: impl Into<String>) -> GeometryError {
    GeometryError::MeshProcessingError(message.into())
}

fn parse_float(value: Option<&str>, line_number: usize, field: &str) -> Result<f32> {
    value
        .ok_or_else(|| obj_error(format!("line {line_number}: missing {field}")))?
        .parse::<f32>()
        .map_err(|error| obj_error(format!("line {line_number}: invalid {field}: {error}")))
}

fn parse_index(value: &str, count: usize, line_number: usize, field: &str) -> Result<usize> {
    let raw = value
        .parse::<i64>()
        .map_err(|error| obj_error(format!("line {line_number}: invalid {field} index: {error}")))?;

    if raw == 0 {
        return Err(obj_error(format!("line {line_number}: OBJ indices cannot be zero")));
    }

    let resolved = if raw > 0 {
        raw - 1
    } else {
        count as i64 + raw
    };

    if resolved < 0 || resolved >= count as i64 {
        return Err(obj_error(format!(
            "line {line_number}: {field} index {raw} is outside the available range"
        )));
    }

    Ok(resolved as usize)
}

fn parse_corner(
    token: &str,
    vertex_count: usize,
    uv_count: usize,
    normal_count: usize,
    line_number: usize,
) -> Result<CornerKey> {
    let mut fields = token.split('/');
    let vertex = fields
        .next()
        .ok_or_else(|| obj_error(format!("line {line_number}: empty face corner")))?;
    let uv = fields.next();
    let normal = fields.next();

    if fields.next().is_some() {
        return Err(obj_error(format!(
            "line {line_number}: face corner has too many slash-separated fields"
        )));
    }

    let vertex = parse_index(vertex, vertex_count, line_number, "vertex")?;
    let uv = uv
        .filter(|value| !value.is_empty())
        .map(|value| parse_index(value, uv_count, line_number, "UV"))
        .transpose()?;
    let normal = normal
        .filter(|value| !value.is_empty())
        .map(|value| parse_index(value, normal_count, line_number, "normal"))
        .transpose()?;

    Ok((vertex, uv, normal))
}

fn parse_obj<R: BufRead>(reader: R) -> Result<Mesh> {
    let mut positions: Vec<Point3<f32>> = Vec::new();
    let mut uvs: Vec<(f32, f32)> = Vec::new();
    let mut source_normals: Vec<Vector3<f32>> = Vec::new();
    let mut mesh = Mesh::new();
    let mut corner_map: HashMap<CornerKey, u32> = HashMap::new();
    let mut any_uv = false;
    let mut any_normal = false;
    let mut missing_normal = false;

    for (line_index, line_result) in reader.lines().enumerate() {
        let line_number = line_index + 1;
        let line = line_result
            .map_err(|error| obj_error(format!("line {line_number}: read failed: {error}")))?;
        let mut fields = line.split_whitespace();
        let Some(directive) = fields.next() else {
            continue;
        };

        match directive {
            "v" => {
                let x = parse_float(fields.next(), line_number, "vertex x")?;
                let y = parse_float(fields.next(), line_number, "vertex y")?;
                let z = parse_float(fields.next(), line_number, "vertex z")?;
                positions.push(Point3::new(x, y, z));
            }
            "vt" => {
                let u = parse_float(fields.next(), line_number, "UV u")?;
                let v = parse_float(fields.next(), line_number, "UV v")?;
                uvs.push((u, v));
            }
            "vn" => {
                let x = parse_float(fields.next(), line_number, "normal x")?;
                let y = parse_float(fields.next(), line_number, "normal y")?;
                let z = parse_float(fields.next(), line_number, "normal z")?;
                source_normals.push(Vector3::new(x, y, z).normalize());
            }
            "f" => {
                let face_tokens: Vec<&str> = fields.collect();
                if face_tokens.len() < 3 {
                    return Err(obj_error(format!(
                        "line {line_number}: face requires at least three corners"
                    )));
                }

                let mut corners = Vec::with_capacity(face_tokens.len());
                for token in face_tokens {
                    let key = parse_corner(
                        token,
                        positions.len(),
                        uvs.len(),
                        source_normals.len(),
                        line_number,
                    )?;

                    let index = if let Some(&existing) = corner_map.get(&key) {
                        existing
                    } else {
                        let index = mesh.vertices.len() as u32;
                        mesh.vertices.push(positions[key.0]);
                        if let Some(uv_index) = key.1 {
                            mesh.uvs.push(uvs[uv_index]);
                            any_uv = true;
                        } else {
                            mesh.uvs.push((0.0, 0.0));
                        }
                        if let Some(normal_index) = key.2 {
                            mesh.normals.push(source_normals[normal_index]);
                            any_normal = true;
                        } else {
                            mesh.normals.push(Vector3::zeros());
                            missing_normal = true;
                        }
                        corner_map.insert(key, index);
                        index
                    };
                    corners.push(index);
                }

                for corner in 1..corners.len() - 1 {
                    mesh.indices.extend_from_slice(&[corners[0], corners[corner], corners[corner + 1]]);
                }
            }
            "o" | "g" | "s" | "mtllib" | "usemtl" => {
                // Scene/material metadata is outside this loader's contract.
            }
            "#" | "" => {}
            _ => {
                // Unknown OBJ extensions are ignored rather than guessed.
            }
        }
    }

    if mesh.indices.is_empty() {
        return Err(obj_error("OBJ contains no triangular faces"));
    }

    if !any_uv {
        mesh.uvs.clear();
    }
    if !any_normal {
        mesh.normals.clear();
    } else if missing_normal {
        mesh.compute_normals();
    }

    Ok(mesh)
}

/// Load a mesh from an OBJ file.
///
/// The returned mesh contains triangulated geometry. OBJ material, group,
/// smoothing, and scene metadata are intentionally not represented.
pub fn load_obj(path: &Path) -> Result<Mesh> {
    let file = File::open(path)?;
    parse_obj(BufReader::new(file)).map_err(|error| {
        obj_error(format!("{}: {}", path.display(), error))
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Cursor;

    #[test]
    fn parses_quad_with_attributes_and_triangulates() {
        let input = b"v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\nvt 0 0\nvt 1 0\nvt 1 1\nvt 0 1\nvn 0 0 1\nf 1/1/1 2/2/1 3/3/1 4/4/1\n";
        let mesh = parse_obj(Cursor::new(input)).unwrap();
        assert_eq!(mesh.vertex_count(), 4);
        assert_eq!(mesh.triangle_count(), 2);
        assert_eq!(mesh.uvs.len(), 4);
        assert_eq!(mesh.normals.len(), 4);
    }

    #[test]
    fn supports_negative_indices() {
        let input = b"v 0 0 0\nv 1 0 0\nv 0 1 0\nf -3 -2 -1\n";
        let mesh = parse_obj(Cursor::new(input)).unwrap();
        assert_eq!(mesh.triangle_count(), 1);
        assert_eq!(mesh.vertices[0], Point3::new(0.0, 0.0, 0.0));
    }

    #[test]
    fn rejects_out_of_range_indices() {
        let input = b"v 0 0 0\nf 1 2 3\n";
        assert!(parse_obj(Cursor::new(input)).is_err());
    }
}
