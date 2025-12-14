//! Level of Detail (LOD) generation

use crate::geometry::Mesh;
use crate::Result;

/// LOD generator for creating multiple levels of detail
pub struct LodGenerator {
    levels: Vec<f32>,
}

impl LodGenerator {
    pub fn new() -> Self {
        Self {
            levels: vec![1.0, 0.5, 0.25, 0.125],
        }
    }

    pub fn with_levels(mut self, levels: Vec<f32>) -> Self {
        self.levels = levels;
        self
    }

    /// Generate LOD chain for a mesh
    pub fn generate(&self, mesh: &Mesh) -> Result<Vec<Mesh>> {
        let mut lods = Vec::new();

        for &ratio in &self.levels {
            let target_triangles = (mesh.triangle_count() as f32 * ratio) as usize;
            // TODO: Use mesh simplification to create LOD
            lods.push(mesh.clone());
        }

        Ok(lods)
    }

    /// Calculate appropriate LOD level based on distance
    pub fn select_lod(distance: f32, thresholds: &[f32]) -> usize {
        for (i, &threshold) in thresholds.iter().enumerate() {
            if distance < threshold {
                return i;
            }
        }
        thresholds.len()
    }
}

impl Default for LodGenerator {
    fn default() -> Self {
        Self::new()
    }
}
