use pyo3::prelude::*;
use image::{GenericImageView, ImageBuffer, Luma};
use ndarray::Array2;
use rayon::prelude::*;

// Procedural generation imports
use noise::{NoiseFn, Perlin, OpenSimplex, Fbm, MultiFractal};
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha20Rng;

#[allow(unused_imports)]
use pyo3::types::PyModule;

/// Converts an image implementing GenericImageView to a normalized f32 array
/// This explicitly uses the GenericImageView trait for efficient pixel access
fn image_to_array<I>(img: &I) -> Array2<f32>
where
    I: GenericImageView<Pixel = Luma<u8>>,
{
    let (width, height) = img.dimensions();
    let mut arr = Array2::<f32>::zeros((height as usize, width as usize));

    // Use GenericImageView's efficient enumerate_pixels iterator
    for (x, y, pixel) in img.enumerate_pixels() {
        arr[[y as usize, x as usize]] = pixel[0] as f32 / 255.0;
    }

    arr
}

/// High-end sharpness analysis using multiple industry-standard metrics
///
/// This production-grade implementation combines:
/// 1. Gradient Variance (Laplacian) - edge strength analysis
/// 2. Tenengrad Metric - gradient magnitude statistics
/// 3. Brenner Metric - focus measurement
/// 4. Sobel Operators - directional edge detection
///
/// Returns comprehensive sharpness score optimized for SDXL/diffusion outputs
#[pyfunction]
fn rs_sharpness_score(path: &str) -> PyResult<f32> {
    let img = image::open(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(
            format!("Failed to open image: {}", e)
        ))?;

    let gray_img = img.to_luma8();
    let (width, height) = gray_img.dimensions();

    // Validate image dimensions
    if width < 3 || height < 3 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "Image too small for sharpness analysis (min 3x3)"
        ));
    }

    // Convert using GenericImageView-based conversion
    let arr = image_to_array(&gray_img);

    // Metric 1: Laplacian Variance (Industry standard for sharpness)
    let laplacian_score = compute_laplacian_variance(&arr, width as usize, height as usize);

    // Metric 2: Tenengrad (Gradient magnitude - used in autofocus systems)
    let tenengrad_score = compute_tenengrad(&arr, width as usize, height as usize);

    // Metric 3: Brenner Focus Measure (Used in microscopy)
    let brenner_score = compute_brenner(&arr, width as usize, height as usize);

    // Metric 4: Sobel Variance (Professional edge detection)
    let sobel_score = compute_sobel_variance(&arr, width as usize, height as usize);

    // Weighted combination calibrated for AI-generated imagery
    // Laplacian: 35% (general sharpness)
    // Tenengrad: 30% (edge clarity)
    // Sobel: 25% (directional edges)
    // Brenner: 10% (fine detail)
    let combined_score =
        laplacian_score * 0.35 +
        tenengrad_score * 0.30 +
        sobel_score * 0.25 +
        brenner_score * 0.10;

    Ok(combined_score.max(0.0).min(1.0))
}

/// Laplacian variance - measures second derivative (edge strength)
fn compute_laplacian_variance(arr: &Array2<f32>, width: usize, height: usize) -> f32 {
    let mut laplacian_values = Vec::with_capacity((width - 2) * (height - 2));

    for y in 1..(height - 1) {
        for x in 1..(width - 1) {
            // 3x3 Laplacian kernel:
            // [ 0  1  0]
            // [ 1 -4  1]
            // [ 0  1  0]
            let lap =
                arr[[y - 1, x]] + arr[[y + 1, x]] +
                arr[[y, x - 1]] + arr[[y, x + 1]] -
                4.0 * arr[[y, x]];
            laplacian_values.push(lap);
        }
    }

    if laplacian_values.is_empty() {
        return 0.0;
    }

    let mean: f32 = laplacian_values.iter().sum::<f32>() / laplacian_values.len() as f32;
    let variance: f32 = laplacian_values.iter()
        .map(|&v| (v - mean).powi(2))
        .sum::<f32>() / laplacian_values.len() as f32;

    // Normalize variance to [0, 1] range (calibrated for 0-1 normalized images)
    (variance * 50.0).min(1.0)
}

/// Tenengrad metric - sum of squared gradient magnitudes above threshold
fn compute_tenengrad(arr: &Array2<f32>, width: usize, height: usize) -> f32 {
    let threshold = 0.05; // Calibrated for normalized images

    let sum: f32 = (1..(height - 1))
        .into_par_iter()
        .map(|y| {
            let mut row_sum = 0.0f32;
            for x in 1..(width - 1) {
                // Sobel operators
                let gx = sobel_x(arr, x, y);
                let gy = sobel_y(arr, x, y);
                let magnitude = (gx * gx + gy * gy).sqrt();

                if magnitude > threshold {
                    row_sum += magnitude * magnitude;
                }
            }
            row_sum
        })
        .sum();

    let pixels = ((width - 2) * (height - 2)) as f32;
    // Normalize to [0, 1]
    (sum / (pixels * 0.1)).min(1.0)
}

/// Brenner focus measure - horizontal derivative squared
fn compute_brenner(arr: &Array2<f32>, width: usize, height: usize) -> f32 {
    let mut sum = 0.0f32;

    for y in 0..height {
        for x in 0..(width - 2) {
            let diff = arr[[y, x + 2]] - arr[[y, x]];
            sum += diff * diff;
        }
    }

    let pixels = (width - 2) * height;
    // Normalize to [0, 1]
    (sum / (pixels as f32 * 0.2)).min(1.0)
}

/// Sobel variance - variance of Sobel edge magnitudes
fn compute_sobel_variance(arr: &Array2<f32>, width: usize, height: usize) -> f32 {
    let mut magnitudes = Vec::with_capacity((width - 2) * (height - 2));

    for y in 1..(height - 1) {
        for x in 1..(width - 1) {
            let gx = sobel_x(arr, x, y);
            let gy = sobel_y(arr, x, y);
            let magnitude = (gx * gx + gy * gy).sqrt();
            magnitudes.push(magnitude);
        }
    }

    if magnitudes.is_empty() {
        return 0.0;
    }

    let mean: f32 = magnitudes.iter().sum::<f32>() / magnitudes.len() as f32;
    let variance: f32 = magnitudes.iter()
        .map(|&m| (m - mean).powi(2))
        .sum::<f32>() / magnitudes.len() as f32;

    // Normalize to [0, 1]
    (variance * 10.0).min(1.0)
}

/// Sobel operator for X direction (horizontal edges)
#[inline]
fn sobel_x(arr: &Array2<f32>, x: usize, y: usize) -> f32 {
    // Sobel X kernel:
    // [-1  0  1]
    // [-2  0  2]
    // [-1  0  1]
    -arr[[y - 1, x - 1]] - 2.0 * arr[[y, x - 1]] - arr[[y + 1, x - 1]]
     + arr[[y - 1, x + 1]] + 2.0 * arr[[y, x + 1]] + arr[[y + 1, x + 1]]
}

/// Sobel operator for Y direction (vertical edges)
#[inline]
fn sobel_y(arr: &Array2<f32>, x: usize, y: usize) -> f32 {
    // Sobel Y kernel:
    // [-1 -2 -1]
    // [ 0  0  0]
    // [ 1  2  1]
    -arr[[y - 1, x - 1]] - 2.0 * arr[[y - 1, x]] - arr[[y - 1, x + 1]]
     + arr[[y + 1, x - 1]] + 2.0 * arr[[y + 1, x]] + arr[[y + 1, x + 1]]
}

// ============================================================================
// Procedural Generation Functions
// ============================================================================

/// Generate Perlin noise texture for procedural assets
///
/// Perlin noise is smooth, continuous noise ideal for natural-looking textures,
/// clouds, terrain, and organic patterns.
///
/// Args:
///     width: Texture width in pixels
///     height: Texture height in pixels
///     scale: Noise frequency scale (smaller = larger features)
///     octaves: Number of noise layers (more = more detail)
///     seed: Random seed for reproducibility
///
/// Returns:
///     Flat Vec<u8> of grayscale pixel values (row-major order)
#[pyfunction]
fn generate_perlin_texture(
    width: u32,
    height: u32,
    scale: f64,
    octaves: usize,
    seed: u64,
) -> PyResult<Vec<u8>> {
    let perlin = Perlin::new(seed as u32);
    let mut pixels = Vec::with_capacity((width * height) as usize);

    let scale = scale.max(0.001); // Prevent division by zero

    for y in 0..height {
        for x in 0..width {
            let nx = x as f64 / width as f64 * scale;
            let ny = y as f64 / height as f64 * scale;

            // Multi-octave sampling for richer detail
            let mut value = 0.0;
            let mut amplitude = 1.0;
            let mut frequency = 1.0;
            let mut max_value = 0.0;

            for _ in 0..octaves {
                value += perlin.get([nx * frequency, ny * frequency]) * amplitude;
                max_value += amplitude;
                amplitude *= 0.5;
                frequency *= 2.0;
            }

            // Normalize to [0, 1] then to [0, 255]
            value = value / max_value;
            let normalized = ((value + 1.0) * 0.5).clamp(0.0, 1.0);
            pixels.push((normalized * 255.0) as u8);
        }
    }

    Ok(pixels)
}

/// Generate Simplex noise pattern for organic textures
///
/// Simplex noise (OpenSimplex variant) has fewer directional artifacts than Perlin,
/// making it ideal for organic patterns, water, fire, and smoke effects.
///
/// Args:
///     width: Texture width in pixels
///     height: Texture height in pixels
///     frequency: Noise frequency (higher = smaller features)
///     seed: Random seed for reproducibility
///
/// Returns:
///     Flat Vec<u8> of grayscale pixel values
#[pyfunction]
fn generate_simplex_pattern(
    width: u32,
    height: u32,
    frequency: f64,
    seed: u64,
) -> PyResult<Vec<u8>> {
    let simplex = OpenSimplex::new(seed as u32);
    let mut pixels = Vec::with_capacity((width * height) as usize);

    let frequency = frequency.max(0.001);

    for y in 0..height {
        for x in 0..width {
            let nx = x as f64 * frequency;
            let ny = y as f64 * frequency;

            let value = simplex.get([nx, ny]);

            // Normalize from [-1, 1] to [0, 255]
            let normalized = ((value + 1.0) * 0.5).clamp(0.0, 1.0);
            pixels.push((normalized * 255.0) as u8);
        }
    }

    Ok(pixels)
}

/// Generate Fractional Brownian Motion (FBM) heightmap for terrain and detail
///
/// FBM combines multiple octaves of noise with specific parameters to create
/// natural-looking terrain, clouds, and complex organic patterns.
///
/// Args:
///     width: Heightmap width in pixels
///     height: Heightmap height in pixels
///     octaves: Number of noise layers (typical: 4-8)
///     lacunarity: Frequency multiplier per octave (typical: 2.0)
///     persistence: Amplitude multiplier per octave (typical: 0.5)
///     seed: Random seed for reproducibility
///
/// Returns:
///     Flat Vec<f32> of height values in [0, 1]
#[pyfunction]
fn generate_fbm_heightmap(
    width: u32,
    height: u32,
    octaves: usize,
    lacunarity: f64,
    persistence: f64,
    seed: u64,
) -> PyResult<Vec<f32>> {
    // Create FBM noise with custom parameters
    let fbm = Fbm::<Perlin>::new(seed as u32)
        .set_octaves(octaves)
        .set_frequency(1.0)
        .set_lacunarity(lacunarity)
        .set_persistence(persistence);

    let mut heights = Vec::with_capacity((width * height) as usize);

    for y in 0..height {
        for x in 0..width {
            // Normalize coordinates to [0, 1]
            let nx = x as f64 / width as f64;
            let ny = y as f64 / height as f64;

            let value = fbm.get([nx * 4.0, ny * 4.0]); // Scale for interesting features

            // Normalize from approximately [-1, 1] to [0, 1]
            // FBM range depends on octaves/persistence, so we clamp
            let normalized = ((value + 1.0) * 0.5).clamp(0.0, 1.0) as f32;
            heights.push(normalized);
        }
    }

    Ok(heights)
}

/// Generate variation seeds for reproducible asset generation
///
/// Creates a sequence of pseudo-random seeds derived from a base seed,
/// ensuring reproducible generation across multiple variations.
///
/// Args:
///     base_seed: Starting seed value
///     count: Number of variation seeds to generate
///
/// Returns:
///     Vec<u64> of variation seeds
#[pyfunction]
fn generate_variation_seeds(base_seed: u64, count: usize) -> PyResult<Vec<u64>> {
    let mut rng = ChaCha20Rng::seed_from_u64(base_seed);
    let seeds: Vec<u64> = (0..count).map(|_| rng.gen()).collect();
    Ok(seeds)
}

/// Generate Perlin noise with custom amplitude mapping
///
/// Advanced Perlin generation with remapping function for specific use cases
/// like creating masks, blend maps, or artistic effects.
///
/// Args:
///     width: Texture width
///     height: Texture height
///     scale: Base frequency scale
///     octaves: Detail layers
///     seed: Random seed
///     contrast: Contrast adjustment (1.0 = normal, >1.0 = more contrast)
///     brightness: Brightness offset (-1.0 to 1.0)
///
/// Returns:
///     Flat Vec<u8> of remapped pixel values
#[pyfunction]
fn generate_perlin_advanced(
    width: u32,
    height: u32,
    scale: f64,
    octaves: usize,
    seed: u64,
    contrast: f64,
    brightness: f64,
) -> PyResult<Vec<u8>> {
    let perlin = Perlin::new(seed as u32);
    let mut pixels = Vec::with_capacity((width * height) as usize);

    let scale = scale.max(0.001);

    for y in 0..height {
        for x in 0..width {
            let nx = x as f64 / width as f64 * scale;
            let ny = y as f64 / height as f64 * scale;

            let mut value = 0.0;
            let mut amplitude = 1.0;
            let mut frequency = 1.0;
            let mut max_value = 0.0;

            for _ in 0..octaves {
                value += perlin.get([nx * frequency, ny * frequency]) * amplitude;
                max_value += amplitude;
                amplitude *= 0.5;
                frequency *= 2.0;
            }

            value = value / max_value;

            // Apply contrast and brightness
            value = (value * contrast) + brightness;

            // Normalize to [0, 1] then [0, 255]
            let normalized = ((value + 1.0) * 0.5).clamp(0.0, 1.0);
            pixels.push((normalized * 255.0) as u8);
        }
    }

    Ok(pixels)
}

#[pymodule]
fn vmf_validator(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Validation functions
    m.add_function(wrap_pyfunction!(rs_sharpness_score, m)?)?;

    // Procedural generation functions
    m.add_function(wrap_pyfunction!(generate_perlin_texture, m)?)?;
    m.add_function(wrap_pyfunction!(generate_simplex_pattern, m)?)?;
    m.add_function(wrap_pyfunction!(generate_fbm_heightmap, m)?)?;
    m.add_function(wrap_pyfunction!(generate_variation_seeds, m)?)?;
    m.add_function(wrap_pyfunction!(generate_perlin_advanced, m)?)?;

    Ok(())
}