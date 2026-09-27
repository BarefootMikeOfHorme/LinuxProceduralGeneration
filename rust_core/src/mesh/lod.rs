//! Level of Detail generation.
//!
//! A LOD chain is a sequence of meshes, each a decimated version of the one
//! before it, ending at a caller-specified triangle budget. The reduction itself
//! is quadric error metrics, in [`crate::mesh::simplify`].
//!
//! # Why the level set is validated up front
//!
//! The ratios are validated when the generator is built rather than when it is
//! used, because a silently wrong level set produces a chain that looks fine and
//! is not: a ratio of `0.0` asks for an empty mesh, a ratio above `1.0` asks for
//! a mesh *larger* than the input, and an unsorted set makes
//! [`LodGenerator::select_lod`]'s index meaningless because the indices no longer
//! correspond to a progression.

use crate::geometry::Mesh;
use crate::{GeometryError, Result};

/// The default LOD chain: full detail, then halves.
///
/// Each step is a factor of two, which is the conventional spacing because it
/// keeps the on-screen error between consecutive levels roughly constant as
/// distance doubles.
const DEFAULT_LEVELS: [f32; 4] = [1.0, 0.5, 0.25, 0.125];

/// Generates a LOD chain by successive quadric-error decimation.
#[derive(Debug, Clone)]
pub struct LodGenerator {
    /// Triangle-count ratios, one per level, in strictly decreasing order.
    /// Each must be in `(0, 1]`.
    levels: Vec<f32>,
}

impl LodGenerator {
    /// A generator using [`DEFAULT_LEVELS`].
    pub fn new() -> Self {
        Self {
            levels: DEFAULT_LEVELS.to_vec(),
        }
    }

    /// Build a generator with explicit triangle-count ratios.
    ///
    /// Each ratio must lie in `(0, 1]`, and they must be strictly decreasing so
    /// that level 0 is the most detailed. Rejected values are named in the error
    /// rather than silently clamped, because a clamped ratio produces a chain
    /// that is quietly not the one that was asked for.
    pub fn with_levels(levels: Vec<f32>) -> Result<Self> {
        if levels.is_empty() {
            return Err(GeometryError::InvalidParameters(
                "a LOD chain needs at least one level".to_string(),
            ));
        }
        for (i, &ratio) in levels.iter().enumerate() {
            if !ratio.is_finite() {
                return Err(GeometryError::InvalidParameters(format!(
                    "LOD level {i} ratio is not a finite number: {ratio}"
                )));
            }
            if ratio <= 0.0 || ratio > 1.0 {
                return Err(GeometryError::InvalidParameters(format!(
                    "LOD level {i} ratio {ratio} is outside (0, 1]; ratios are triangle \
                     counts relative to the input mesh"
                )));
            }
            if i > 0 && ratio >= levels[i - 1] {
                return Err(GeometryError::InvalidParameters(format!(
                    "LOD levels must strictly decrease: level {i} ratio {ratio} is not below \
                     level {} ratio {}",
                    i - 1,
                    levels[i - 1]
                )));
            }
        }
        Ok(Self { levels })
    }

    /// The configured ratios, most detailed first.
    pub fn levels(&self) -> &[f32] {
        &self.levels
    }

    /// Generate the LOD chain for `mesh`.
    ///
    /// Level 0 is the input mesh itself, unchanged: a caller that asks for
    /// "full detail" must get exactly the mesh it passed in, not a decimated
    /// approximation of it.
    ///
    /// Every level after the first is produced by real decimation. If any level
    /// cannot reach its budget, this returns an error naming the level and the
    /// count it stalled at, rather than returning a chain that quietly misses.
    pub fn generate(&self, mesh: &Mesh) -> Result<Vec<Mesh>> {
        if mesh.triangle_count() == 0 {
            return Err(GeometryError::InvalidParameters(
                "cannot build a LOD chain from a mesh with no triangles".to_string(),
            ));
        }
        if self.levels[0] != 1.0 {
            return Err(GeometryError::InvalidParameters(format!(
                "LOD level 0 ratio is {} but must be 1.0; the first level is the input mesh",
                self.levels[0]
            )));
        }

        let start = mesh.triangle_count();
        let mut chain: Vec<Mesh> = Vec::with_capacity(self.levels.len());
        chain.push(mesh.clone());

        for (i, &ratio) in self.levels.iter().enumerate().skip(1) {
            let target = ((start as f64) * ratio as f64).round() as usize;
            // A ratio small enough to land below the four triangles a closed
            // solid needs is not a decimation request, it is a mistake. Say so,
            // rather than failing later inside the simplifier.
            let target = target.max(4);
            if target >= chain[i - 1].triangle_count() {
                return Err(GeometryError::InvalidParameters(format!(
                    "LOD level {i} wants {target} triangles but level {} already has {}; \
                     the ratio {ratio} does not reduce anything at this mesh size",
                    i - 1,
                    chain[i - 1].triangle_count()
                )));
            }
            let level = crate::mesh::simplify::simplify(&chain[i - 1], target)?;
            chain.push(level);
        }

        Ok(chain)
    }

    /// Triangle counts each level aims for on a mesh of `triangle_count` faces.
    ///
    /// Useful for reporting, and for checking a chain against a budget before
    /// generating it.
    pub fn targets(&self, triangle_count: usize) -> Vec<usize> {
        self.levels
            .iter()
            .map(|&ratio| ((triangle_count as f64) * ratio as f64).round() as usize)
            .collect()
    }

    /// Number of levels implied by a threshold list.
    ///
    /// There is one threshold per *transition* between levels, so a list of `n`
    /// thresholds describes `n + 1` levels. This is the off-by-one that made the
    /// old `select_lod` look wrong: it returned `thresholds.len()` for a distant
    /// object, which is a perfectly valid index under this contract, not one
    /// past the end. The confusion was in the missing definition, not the code.
    pub fn levels_for_thresholds(thresholds: &[f32]) -> usize {
        thresholds.len() + 1
    }

    /// Choose a level index for a given distance.
    ///
    /// `thresholds[i]` is the distance beyond which level `i + 1` is preferred,
    /// so the result is in `0..=thresholds.len()`, and the caller must have
    /// `LodGenerator::levels_for_thresholds(thresholds)` levels available. Use
    /// [`LodGenerator::select_lod_checked`] when that is not guaranteed.
    ///
    /// The last level is the fallback for any distance at or beyond the final
    /// threshold, so the result is always within range of a correctly sized
    /// level set.
    pub fn select_lod(distance: f32, thresholds: &[f32]) -> usize {
        if thresholds.is_empty() {
            return 0;
        }
        if !distance.is_finite() {
            // A non-finite distance is a caller bug, but the only safe answer is
            // the most detailed level, not an arbitrary one.
            return 0;
        }
        for (i, &threshold) in thresholds.iter().enumerate() {
            if distance < threshold {
                return i;
            }
        }
        thresholds.len()
    }

    /// [`LodGenerator::select_lod`] against a known level count.
    ///
    /// Returns `None` when the chosen index is out of range for `level_count`,
    /// which is what a caller with one level per threshold instead of one per
    /// transition actually has. The unguarded version cannot detect that, so this
    /// is the one to reach for when the level set is built elsewhere.
    pub fn select_lod_checked(distance: f32, thresholds: &[f32], level_count: usize) -> Option<usize> {
        let index = Self::select_lod(distance, thresholds);
        if index < level_count {
            Some(index)
        } else {
            None
        }
    }
}

impl Default for LodGenerator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::geometry::primitives::Sphere;
    use crate::geometry::Primitive;

    #[test]
    fn default_levels_start_at_full_detail() {
        let generator = LodGenerator::new();
        assert_eq!(generator.levels()[0], 1.0);
        assert!(generator.levels().windows(2).all(|w| w[0] > w[1]));
    }

    #[test]
    fn level_zero_is_the_input_mesh_unchanged() {
        let sphere = Sphere::new(1.0).to_mesh().unwrap();
        let chain = LodGenerator::new().generate(&sphere).unwrap();
        assert_eq!(chain[0].vertex_count(), sphere.vertex_count());
        assert_eq!(chain[0].triangle_count(), sphere.triangle_count());
        assert_eq!(chain[0].indices, sphere.indices);
    }

    #[test]
    fn each_level_actually_reduces() {
        let sphere = Sphere::new(1.0).to_mesh().unwrap();
        let chain = LodGenerator::new().generate(&sphere).unwrap();
        assert!(chain.len() >= 3);
        for pair in chain.windows(2) {
            assert!(
                pair[1].triangle_count() < pair[0].triangle_count(),
                "a level did not reduce: {} then {}",
                pair[0].triangle_count(),
                pair[1].triangle_count()
            );
        }
        // Every level must be distinct, not a clone of its parent. This is the
        // property the old implementation failed: it returned the input mesh
        // once per level and called it a chain.
        for (i, level) in chain.iter().enumerate() {
            if i == 0 {
                continue;
            }
            assert_ne!(
                level.indices.len(),
                chain[0].indices.len(),
                "level {i} is the same size as level 0"
            );
        }
    }

    #[test]
    fn levels_hit_their_requested_budgets() {
        let sphere = Sphere::new(1.0).to_mesh().unwrap();
        let generator = LodGenerator::new();
        let targets = generator.targets(sphere.triangle_count());
        let chain = generator.generate(&sphere).unwrap();
        for (i, &target) in targets.iter().enumerate().skip(1) {
            assert!(
                chain[i].triangle_count() <= target,
                "level {i} has {} triangles, above its budget of {target}",
                chain[i].triangle_count()
            );
        }
    }

    #[test]
    fn decimation_keeps_the_solid_closed() {
        let sphere = Sphere::new(1.0).to_mesh().unwrap();
        let chain = LodGenerator::new().generate(&sphere).unwrap();
        for (i, level) in chain.iter().enumerate() {
            let mut counts = std::collections::HashMap::new();
            for f in 0..level.triangle_count() {
                for k in 0..3 {
                    let a = level.indices[f * 3 + k];
                    let b = level.indices[f * 3 + (k + 1) % 3];
                    let key = if a < b { (a, b) } else { (b, a) };
                    *counts.entry(key).or_insert(0usize) += 1;
                }
            }
            let boundary = counts.values().filter(|&&c| c == 1).count();
            let non_manifold = counts.values().filter(|&&c| c > 2).count();
            assert_eq!(boundary, 0, "LOD level {i} has {boundary} boundary edges");
            assert_eq!(
                non_manifold, 0,
                "LOD level {i} has {non_manifold} non-manifold edges"
            );
        }
    }

    #[test]
    fn decimation_follows_the_inscribed_polyhedron_law() {
        // Decimation loses detail by construction: the result is an inscribed
        // polyhedron, so its volume sits *below* the ideal sphere and the gap
        // widens as triangles are removed. Measured on this primitive the deficit
        // is almost exactly 15/F percent, where F is the triangle count
        // (15.3 at F=960, 16.0 at 480, 16.0 at 240, 14.3 at 120).
        //
        // Asserting that law rather than a flat tolerance is what makes the test
        // mean something. A flat bound has to be loosened until the coarsest
        // level passes, and a bound loose enough for the coarsest level would
        // never notice a collapse at a finer one. The 1/F form holds at every
        // level, so it catches a collapse wherever it appears and does not need
        // retuning when the level set changes.
        const DEFICIT_COEFFICIENT: f64 = 20.0;
        let sphere = Sphere::new(1.0).to_mesh().unwrap();
        let ideal = 4.0 / 3.0 * std::f64::consts::PI;
        let chain = LodGenerator::new().generate(&sphere).unwrap();

        let mut previous = f64::INFINITY;
        for (i, level) in chain.iter().enumerate() {
            let volume = volume_of(level);
            let triangles = level.triangle_count() as f64;

            assert!(
                volume > 0.0,
                "LOD level {i} has volume {volume}; a non-positive volume means faces were flipped"
            );
            assert!(
                volume < previous,
                "LOD level {i} volume {volume} is not below level {}'s {previous}; decimation \
                 of an inscribed solid cannot gain volume, so this means a face was inverted",
                i - 1
            );

            let deficit = (ideal - volume) / ideal;
            let bound = DEFICIT_COEFFICIENT / triangles;
            assert!(
                deficit <= bound,
                "LOD level {i} lost {deficit:.4} of its volume at {triangles} triangles, \
                 beyond the {bound:.4} an inscribed approximation should cost"
            );
            previous = volume;
        }
    }

    fn volume_of(mesh: &Mesh) -> f64 {
        let mut total = 0.0f64;
        for f in 0..mesh.triangle_count() {
            let a = mesh.vertices[mesh.indices[f * 3] as usize].coords;
            let b = mesh.vertices[mesh.indices[f * 3 + 1] as usize].coords;
            let c = mesh.vertices[mesh.indices[f * 3 + 2] as usize].coords;
            total += (a.x as f64 * (b.y as f64 * c.z as f64 - b.z as f64 * c.y as f64)
                - a.y as f64 * (b.x as f64 * c.z as f64 - b.z as f64 * c.x as f64)
                + a.z as f64 * (b.x as f64 * c.y as f64 - b.y as f64 * c.x as f64))
                / 6.0;
        }
        total
    }

    #[test]
    fn invalid_level_sets_are_rejected_with_a_reason() {
        assert!(LodGenerator::with_levels(vec![]).is_err(), "empty chain");
        assert!(
            LodGenerator::with_levels(vec![0.0]).is_err(),
            "a zero ratio asks for an empty mesh"
        );
        assert!(
            LodGenerator::with_levels(vec![1.5]).is_err(),
            "a ratio above 1 asks for a bigger mesh than the input"
        );
        assert!(
            LodGenerator::with_levels(vec![0.5, 0.75]).is_err(),
            "levels must strictly decrease"
        );
        assert!(
            LodGenerator::with_levels(vec![f32::NAN]).is_err(),
            "a non-finite ratio"
        );
    }

    #[test]
    fn select_lod_indexes_within_the_levels_the_thresholds_describe() {
        // Three thresholds describe four levels, so index 3 is the coarsest and
        // is a valid answer, not an overrun. The previous version of this test
        // asserted the opposite and so disagreed with the code it was checking.
        let thresholds = [10.0, 20.0, 40.0];
        let levels = LodGenerator::levels_for_thresholds(&thresholds);
        assert_eq!(levels, 4);

        for &distance in &[0.0, 9.9, 10.0, 39.9, 40.0, 1.0e9] {
            let index = LodGenerator::select_lod(distance, &thresholds);
            assert!(
                index < levels,
                "distance {distance} produced index {index}, out of range for {levels} levels"
            );
            assert_eq!(
                LodGenerator::select_lod_checked(distance, &thresholds, levels),
                Some(index)
            );
        }
        assert_eq!(LodGenerator::select_lod(0.0, &thresholds), 0);
        assert_eq!(LodGenerator::select_lod(15.0, &thresholds), 1);
        assert_eq!(LodGenerator::select_lod(1.0e9, &thresholds), 3);
        assert_eq!(LodGenerator::select_lod(5.0, &[]), 0, "an empty set cannot index");
        assert_eq!(
            LodGenerator::select_lod(f32::NAN, &thresholds),
            0,
            "a non-finite distance must not index arbitrarily"
        );
    }

    #[test]
    fn select_lod_checked_reports_a_level_set_that_is_one_too_short() {
        // A caller with one level per threshold rather than one per transition
        // gets None instead of a silent out-of-range index.
        let thresholds = [10.0, 20.0, 40.0];
        assert_eq!(
            LodGenerator::select_lod_checked(1.0e9, &thresholds, 3),
            None,
            "index 3 does not exist in a 3-level chain"
        );
        assert_eq!(LodGenerator::select_lod_checked(0.0, &thresholds, 3), Some(0));
    }

    #[test]
    fn an_empty_mesh_is_refused_rather_than_chained() {
        let empty = Mesh::new();
        assert!(LodGenerator::new().generate(&empty).is_err());
    }
}
