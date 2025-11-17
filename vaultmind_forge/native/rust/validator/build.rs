// Build script for PyO3 version compatibility
// Handles Python 3.13 (native) and 3.14+ (ABI3 forward compatibility)

use std::env;
use std::process::Command;

fn main() {
    // Check if user has already set PYO3_USE_ABI3_FORWARD_COMPATIBILITY
    if env::var("PYO3_USE_ABI3_FORWARD_COMPATIBILITY").is_ok() {
        println!("cargo:warning=PYO3_USE_ABI3_FORWARD_COMPATIBILITY already set by user");
        return;
    }

    // Detect Python version
    let python_version = detect_python_version();

    println!("cargo:warning=Detected Python version: {}", python_version);

    // If Python >= 3.14, enable ABI3 forward compatibility
    if is_python_314_or_higher(&python_version) {
        println!("cargo:warning=Python 3.14+ detected - enabling ABI3 forward compatibility");

        // This tells PyO3's build script to use forward compatibility
        // Must be printed BEFORE pyo3-ffi runs its build script
        println!("cargo:rustc-env=PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1");
    } else {
        println!("cargo:warning=Python 3.13 or lower - using native PyO3 support");
    }

    // Rerun if Python or environment changes
    println!("cargo:rerun-if-env-changed=PYTHON");
    println!("cargo:rerun-if-env-changed=PYO3_PYTHON");
    println!("cargo:rerun-if-env-changed=PYO3_USE_ABI3_FORWARD_COMPATIBILITY");
}

fn detect_python_version() -> String {
    // Try multiple Python executables in order of preference
    let python_commands = vec![
        "python3",
        "python",
        "python3.13",
        "python3.14",
        "py",
    ];

    for cmd in python_commands {
        if let Ok(output) = Command::new(cmd)
            .arg("--version")
            .output()
        {
            if output.status.success() {
                let version_str = String::from_utf8_lossy(&output.stdout);
                // Extract version number (e.g., "Python 3.14.0" -> "3.14.0")
                if let Some(version) = version_str.split_whitespace().nth(1) {
                    return version.to_string();
                }
            }
        }
    }

    // Default assumption
    "3.13.0".to_string()
}

fn is_python_314_or_higher(version_str: &str) -> bool {
    let parts: Vec<&str> = version_str.split('.').collect();

    if parts.len() < 2 {
        return false;
    }

    // Parse major and minor version
    let major: u32 = parts[0].parse().unwrap_or(3);
    let minor: u32 = parts[1].parse().unwrap_or(13);

    // Check if >= 3.14
    major > 3 || (major == 3 && minor >= 14)
}
