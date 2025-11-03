# Vaultmind Forge – Procedural Generation Pipeline Overview
**Codename:** LPG (Lineage-aware Procedural Generation)  
**Purpose:** A modular, schema-driven system for generating, validating, refining, and packaging assets with mythic clarity and operational rigor.

---

## 🔹 Core Pipeline Flow

1. **Schema Loading**
   - Load YAML/JSON schemas with thresholds and conditioning.
   - Merge defaults and runtime overrides (CLI/env).

2. **Asset Generation**
   - `forge_diffusion` generates images/frames with SDXL, ControlNet, IP-Adapter.
   - Outputs include prompt, embeddings, palette, and schema metadata.

3. **Super-Resolution & Enhancement**
   - `forge_sr` runs GAN + Diffusion SR, scores variants, selects best.

4. **Validation & Safety Checks**
   - `forge_validator` aggregates C++ and Rust checks for anatomy, perspective, mesh, PBR, color space, tiling.
   - Failed validations trigger feedback loops.

5. **Feedback Loops**
   - Schema mutated based on rejection reason.
   - Corrective passes applied (e.g., inpainting, seed-locking).

6. **Packaging & Lineage Archiving**
   - `forge_packaging` bundles assets with lineage.json and export presets.
   - `forge_lineage` archives every pass with scores, helper passes, and metadata.

7. **Monitoring & System Safety**
   - `forge_monitor` tracks CPU/GPU/memory, triggers alerts and backoff logic.

---

## 🔹 Modular Components

| Module               | Role                            | Language | Highlights |
|---------------------|----------------------------------|----------|------------|
| forge_agent          | Orchestration & feedback loops  | Python   | Task graph, retries, schema mutation |
| forge_diffusion      | Image/frame generation          | Python   | Multi-pass, conditioning enforcement |
| forge_sr             | Super-resolution & scoring      | Python   | Variant comparison, best-pick logic |
| forge_validator_cpp  | High-speed validation           | C++      | SIMD, AVX2, JSON logs |
| forge_validator_rust | PBR, color, tiling checks       | Rust     | PyO3, structured JSON |
| forge_lineage        | Archive & lineage tracking      | Python   | Gzip JSONL logs, snapshot storage |
| forge_packaging      | Asset bundling                  | Python   | Zip + lineage.json, export presets |
| forge_monitor        | System metrics & alerts         | Python   | Threshold configs, alert flags |

---

## 🔹 Data Structures

- **ValidationReport**: ok, reason, scores, subreports  
- **LineageEntry**: asset_id, status, reason, scores, helper_passes, prompt, conditioning, timestamp, model_version, blobs  
- **Schemas**: storyboard.yaml, pbr_texture.yaml, thresholds.json

---

## 🔹 Observability & Testing

- Per-run logs: `logs/run_<timestamp>/`  
- JSONL files: agent.jsonl, validation.jsonl, lineage.jsonl, monitor.jsonl  
- Minimal tests:
  - Cycle detection in task graph
  - Feedback mapping logic
  - Lineage gzip roundtrip
  - Validator score merging

---

## 🔹 Packaging & Backend Loading

- Rust: built with `maturin`, returns JSON strings via PyO3  
- C++: built with CMake + Ninja, optional AVX/OpenMP, JSON logging via `VMF_LOG_JSON`  
- Python: loads backends via explicit import or ctypes fallback

---

## 🔹 Thresholds & Runtime Overrides

- Hard thresholds for anatomy, perspective, mesh, PBR, temporal consistency  
- CLI/env flags can override schema values (e.g., palette_strength, passes_max)

---

## 🔹 Summary

Vaultmind Forge is a lineage-aware, schema-bound procedural generation pipeline that:
- Generates assets with conditioning and control
- Validates with native speed and structured rigor
- Refines via feedback loops and helper passes
- Archives every decision for study and reproducibility
- Packages assets with metadata and export presets
- Monitors system health and enforces safety

It’s modular, mythic, and built to teach itself from every rejection.