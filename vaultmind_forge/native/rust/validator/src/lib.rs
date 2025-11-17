use pyo3::prelude::*;
use image::{Luma, ImageBuffer};
use ndarray::Array2;
use rayon::prelude::*;

// Procedural generation imports
use noise::{NoiseFn, Perlin, OpenSimplex, Fbm, MultiFractal};
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha20Rng;

#[allow(unused_imports)]
use pyo3::types::PyModule;

/// Converts a Luma ImageBuffer to a normalized f32 array
/// Optimized for fast conversion of grayscale images
fn image_to_array(img: &ImageBuffer<Luma<u8>, Vec<u8>>) -> Array2<f32> {
    let (width, height) = img.dimensions();
    let mut arr = Array2::<f32>::zeros((height as usize, width as usize));

    // Directly iterate over pixels using ImageBuffer's efficient access
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
// Color Fidelity and Quality Metrics
// ============================================================================

/// Analyze color distribution and vibrancy for generated images
///
/// Returns a color fidelity score based on:
/// - Saturation distribution (avoiding washed-out colors)
/// - Color space coverage (utilizing full RGB spectrum)
/// - Hue diversity (varied color palette)
/// - Brightness distribution (avoiding over/under exposure)
///
/// Optimized for AI-generated imagery validation
#[pyfunction]
fn rs_color_fidelity(path: &str) -> PyResult<f32> {
    let img = image::open(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(
            format!("Failed to open image: {}", e)
        ))?;

    let rgb_img = img.to_rgb8();
    let (width, height) = rgb_img.dimensions();
    let total_pixels = (width * height) as f32;

    if total_pixels == 0.0 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "Image has no pixels"
        ));
    }

    // Collect HSV statistics for color analysis
    let mut saturation_values = Vec::with_capacity(total_pixels as usize);
    let mut brightness_values = Vec::with_capacity(total_pixels as usize);
    let mut hue_histogram = vec![0u32; 360]; // 360 degree hue bins

    for pixel in rgb_img.pixels() {
        let (h, s, v) = rgb_to_hsv(pixel[0], pixel[1], pixel[2]);

        saturation_values.push(s);
        brightness_values.push(v);

        // Bin hue into 360 degrees (skip grayscale pixels with s < 0.1)
        if s > 0.1 {
            let hue_bin = (h * 360.0) as usize % 360;
            hue_histogram[hue_bin] += 1;
        }
    }

    // Metric 1: Saturation score (prefer vibrant colors, penalize washed-out)
    let saturation_score = compute_saturation_quality(&saturation_values);

    // Metric 2: Brightness distribution (balanced exposure)
    let brightness_score = compute_brightness_quality(&brightness_values);

    // Metric 3: Hue diversity (varied color palette)
    let hue_diversity_score = compute_hue_diversity(&hue_histogram);

    // Metric 4: Color space coverage (full RGB spectrum usage)
    let coverage_score = compute_color_coverage(&rgb_img);

    // Weighted combination for overall color fidelity
    let combined_score =
        saturation_score * 0.35 +
        brightness_score * 0.25 +
        hue_diversity_score * 0.25 +
        coverage_score * 0.15;

    Ok(combined_score.max(0.0).min(1.0))
}

/// RGB to HSV conversion
fn rgb_to_hsv(r: u8, g: u8, b: u8) -> (f32, f32, f32) {
    let r = r as f32 / 255.0;
    let g = g as f32 / 255.0;
    let b = b as f32 / 255.0;

    let max = r.max(g).max(b);
    let min = r.min(g).min(b);
    let delta = max - min;

    // Value (brightness)
    let v = max;

    // Saturation
    let s = if max == 0.0 { 0.0 } else { delta / max };

    // Hue
    let h = if delta == 0.0 {
        0.0
    } else if max == r {
        ((g - b) / delta) % 6.0
    } else if max == g {
        ((b - r) / delta) + 2.0
    } else {
        ((r - g) / delta) + 4.0
    };

    let h = (h / 6.0 + 1.0) % 1.0; // Normalize to [0, 1]

    (h, s, v)
}

/// Saturation quality - prefer vibrant, avoid washed-out
fn compute_saturation_quality(saturation_values: &[f32]) -> f32 {
    if saturation_values.is_empty() {
        return 0.0;
    }

    let mean_saturation: f32 = saturation_values.iter().sum::<f32>() / saturation_values.len() as f32;

    // Count pixels with good saturation (>0.3)
    let vibrant_pixels = saturation_values.iter().filter(|&&s| s > 0.3).count() as f32;
    let vibrant_ratio = vibrant_pixels / saturation_values.len() as f32;

    // Combine mean saturation with vibrant pixel ratio
    (mean_saturation * 0.6 + vibrant_ratio * 0.4).min(1.0)
}

/// Brightness quality - balanced exposure, avoid clipping
fn compute_brightness_quality(brightness_values: &[f32]) -> f32 {
    if brightness_values.is_empty() {
        return 0.0;
    }

    // Count overexposed (>0.95) and underexposed (<0.05) pixels
    let overexposed = brightness_values.iter().filter(|&&v| v > 0.95).count() as f32;
    let underexposed = brightness_values.iter().filter(|&&v| v < 0.05).count() as f32;
    let total = brightness_values.len() as f32;

    let clipping_ratio = (overexposed + underexposed) / total;

    // Penalize excessive clipping
    let clipping_score = (1.0 - clipping_ratio * 2.0).max(0.0);

    // Check for balanced histogram distribution
    let mean_brightness: f32 = brightness_values.iter().sum::<f32>() / total;
    let balance_score = 1.0 - (mean_brightness - 0.5).abs() * 2.0;

    (clipping_score * 0.6 + balance_score * 0.4).min(1.0)
}

/// Hue diversity - varied color palette
fn compute_hue_diversity(hue_histogram: &[u32]) -> f32 {
    let total_colored_pixels: u32 = hue_histogram.iter().sum();

    if total_colored_pixels == 0 {
        return 0.5; // Grayscale image - neutral score
    }

    // Count non-empty hue bins
    let occupied_bins = hue_histogram.iter().filter(|&&count| count > 0).count() as f32;

    // Diversity score based on bin occupation (more bins = more diverse)
    let diversity = occupied_bins / 360.0;

    // Calculate entropy for distribution uniformity
    let entropy = hue_histogram.iter()
        .filter(|&&count| count > 0)
        .map(|&count| {
            let p = count as f32 / total_colored_pixels as f32;
            -p * p.log2()
        })
        .sum::<f32>();

    // Normalize entropy (max ~8.5 for uniform 360-bin distribution)
    let entropy_score = (entropy / 8.5).min(1.0);

    (diversity * 0.5 + entropy_score * 0.5).min(1.0)
}

/// Color space coverage - full RGB spectrum usage
fn compute_color_coverage(img: &image::RgbImage) -> f32 {
    let mut r_bins = vec![0u32; 16];
    let mut g_bins = vec![0u32; 16];
    let mut b_bins = vec![0u32; 16];

    for pixel in img.pixels() {
        r_bins[(pixel[0] / 16) as usize] += 1;
        g_bins[(pixel[1] / 16) as usize] += 1;
        b_bins[(pixel[2] / 16) as usize] += 1;
    }

    // Count occupied bins in each channel
    let r_coverage = r_bins.iter().filter(|&&c| c > 0).count() as f32 / 16.0;
    let g_coverage = g_bins.iter().filter(|&&c| c > 0).count() as f32 / 16.0;
    let b_coverage = b_bins.iter().filter(|&&c| c > 0).count() as f32 / 16.0;

    ((r_coverage + g_coverage + b_coverage) / 3.0).min(1.0)
}

/// Analyze image contrast using histogram and edge statistics
///
/// Returns contrast quality score based on:
/// - Histogram spread (dynamic range usage)
/// - Local contrast (edge strength)
/// - Tonal distribution (avoiding flat regions)
#[pyfunction]
fn rs_contrast_score(path: &str) -> PyResult<f32> {
    let img = image::open(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(
            format!("Failed to open image: {}", e)
        ))?;

    let gray_img = img.to_luma8();
    let (width, height) = gray_img.dimensions();

    // Build histogram
    let mut histogram = vec![0u32; 256];
    for pixel in gray_img.pixels() {
        histogram[pixel[0] as usize] += 1;
    }

    // Metric 1: Global contrast (histogram spread)
    let global_contrast = compute_global_contrast(&histogram, (width * height) as u32);

    // Metric 2: Local contrast (edge strength from gradient variance)
    let arr = image_to_array(&gray_img);
    let local_contrast = compute_local_contrast(&arr, width as usize, height as usize);

    // Metric 3: Dynamic range (actual luminance range used)
    let dynamic_range = compute_dynamic_range(&histogram);

    // Weighted combination
    let combined_score =
        global_contrast * 0.40 +
        local_contrast * 0.35 +
        dynamic_range * 0.25;

    Ok(combined_score.max(0.0).min(1.0))
}

/// Global contrast from histogram spread
fn compute_global_contrast(histogram: &[u32], total_pixels: u32) -> f32 {
    // Find effective min/max (exclude outliers <1% and >99%)
    let threshold_low = (total_pixels as f32 * 0.01) as u32;
    let threshold_high = (total_pixels as f32 * 0.99) as u32;

    let mut cumulative = 0u32;
    let mut min_val = 0usize;
    let mut max_val = 255usize;

    for (i, &count) in histogram.iter().enumerate() {
        cumulative += count;
        if cumulative >= threshold_low && min_val == 0 {
            min_val = i;
        }
        if cumulative >= threshold_high {
            max_val = i;
            break;
        }
    }

    let range = (max_val - min_val) as f32;
    (range / 255.0).min(1.0)
}

/// Local contrast from gradient statistics
fn compute_local_contrast(arr: &Array2<f32>, width: usize, height: usize) -> f32 {
    let mut gradient_magnitudes = Vec::with_capacity((width - 2) * (height - 2));

    for y in 1..(height - 1) {
        for x in 1..(width - 1) {
            let gx = sobel_x(arr, x, y);
            let gy = sobel_y(arr, x, y);
            let magnitude = (gx * gx + gy * gy).sqrt();
            gradient_magnitudes.push(magnitude);
        }
    }

    if gradient_magnitudes.is_empty() {
        return 0.0;
    }

    let mean: f32 = gradient_magnitudes.iter().sum::<f32>() / gradient_magnitudes.len() as f32;

    // Normalize mean gradient (typical range 0-0.5 for normalized images)
    (mean * 4.0).min(1.0)
}

/// Dynamic range - actual luminance range used
fn compute_dynamic_range(histogram: &[u32]) -> f32 {
    let min_val = histogram.iter().position(|&c| c > 0).unwrap_or(0);
    let max_val = histogram.iter().rposition(|&c| c > 0).unwrap_or(255);

    let range = (max_val - min_val) as f32;
    (range / 255.0).min(1.0)
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
    // Image quality validation functions
    m.add_function(wrap_pyfunction!(rs_sharpness_score, m)?)?;
    m.add_function(wrap_pyfunction!(rs_color_fidelity, m)?)?;
    m.add_function(wrap_pyfunction!(rs_contrast_score, m)?)?;

    // Procedural generation functions
    m.add_function(wrap_pyfunction!(generate_perlin_texture, m)?)?;
    m.add_function(wrap_pyfunction!(generate_simplex_pattern, m)?)?;
    m.add_function(wrap_pyfunction!(generate_fbm_heightmap, m)?)?;
    m.add_function(wrap_pyfunction!(generate_variation_seeds, m)?)?;
    m.add_function(wrap_pyfunction!(generate_perlin_advanced, m)?)?;

    Ok(())
}