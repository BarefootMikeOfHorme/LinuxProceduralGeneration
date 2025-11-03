use pyo3::prelude::*;
use image::GenericImageView;
use ndarray::Array2;
use rayon::prelude::*;

#[allow(unused_imports)]
use pyo3::types::PyModule;

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

    // Convert to f32 array with efficient iteration
    let mut arr = Array2::<f32>::zeros((height as usize, width as usize));
    for (y, mut row) in arr.outer_iter_mut().enumerate() {
        for (x, pixel_val) in row.iter_mut().enumerate() {
            *pixel_val = gray_img.get_pixel(x as u32, y as u32)[0] as f32 / 255.0;
        }
    }

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

#[pymodule]
fn vmf_validator(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rs_sharpness_score, m)?)?;
    Ok(())
}