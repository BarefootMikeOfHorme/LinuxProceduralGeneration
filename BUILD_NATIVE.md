# Building Native Components (C++ + Rust via maturin)

## Quick Start
- C++ (Windows/macOS/Linux):
  - PowerShell: `scripts/build_cpp.ps1 -Release`
- Rust PyO3 (maturin):
  - Install: `pip install maturin`
  - PowerShell: `scripts/build_rust.ps1 -Release`
- Build both: `scripts/build_all.ps1 -Release`

## Output Artifacts
- C++ DLL/SO/DYLIB under `vaultmind_forge/native/cpp/validator/build`
- Rust Python extension installed into current environment by `maturin develop`

## Advanced Options & QoL
- Generators: use Ninja for faster builds (`-G Ninja`) if installed.
- Caches: enable `ccache`/`sccache` for C++ and Rust (`RUSTC_WRAPPER=sccache`).
- Dependency manager: integrate `vcpkg` (Windows) for future libs (e.g., OpenCV/OpenImageIO).
- Cross-platform Python: use `maturin build --release` to produce wheels; combine with `auditwheel`/`delocate` for manylinux/macOS.
- Environments: prefer `uv`/`rye` or `mamba`/`conda` for reproducible Python envs.
- Linux dev: WSL2 on Windows for full GNU toolchain; GPU via CUDA/ROCm if needed.
- SIMD/Parallel: compile with AVX2/AVX512 and OpenMP/TBB for C++; `rayon` in Rust.
- GPU Paths: consider Vulkan (via Kompute), CUDA (cuDNN), or OpenCL backends for validators.
- Preview/IO: tie into FFmpeg (NVENC/AMF/QSV) for video; OpenImageIO for robust image formats.
- Pre-commit: set up `pre-commit` hooks (ruff/black/isort) and CMake format.
- CI: GitHub Actions to build wheels via `maturin-action` and matrix CMake builds.
- Package managers: `vcpkg` manifest mode alongside CMake for deterministic C++ deps.
- Emulators/VMs: QEMU/UTM or Docker for cross-compiling and repeatable builds.

## Troubleshooting
- If Python cannot import `vmf_validator`, ensure `maturin develop` ran in the active environment.
- If the C++ DLL is not found, copy it next to `forge_validator/backends.py` or add its folder to PATH.