<!--
Cursor / AI Assistant Instruction File
When editing code inside VaultMind Forge, load this document as context.
-->


VAULTMIND FORGE – CURSOR INSTRUCTION PROMPT



PURPOSE

This prompt is designed to guide Cursor (or any AI coding assistant) when working inside the vaultmind\_forge project. It encodes the philosophy, architecture, and workflows we’ve defined so far, ensuring consistency, lineage fidelity, and high‑quality outputs.



------------------------------------------------------------

CORE PRINCIPLES

\- Every output is lineage‑aware: store metadata, references, and rejection reasons.

\- Prioritize precision and consistency over speed.

\- Use staged, layered refinement: foundations → generation → enhancement → validation → packaging → archive.

\- Integrate curated feedback loops and dependency graph execution.

\- Support branching, rollback, and reproducibility.

\- Maintain ceremonial clarity: protocols are documented as living scrolls.



------------------------------------------------------------

OUTPUT TYPES

Primary:

\- Manga/Anime Storyboards

\- Game Assets (3D/PBR)

\- Game Environments

\- Character Models

\- Live Video/Cinematics

\- Advertisements

\- Film/Shorts

\- UI Mockups

\- Product Renders

\- Architectural Visualization

\- CAD/C4D Outputs

\- Educational/Scientific Visuals

\- Print/Physical Media



Subcategories:

2D: Illustrations, Concept Art, Line Art, Cel‑Shaded Panels, Pixel Art, Sketches, Blueprints, Technical Diagrams, Posters, Icons, UI Elements

3D: Hard Surface Models, Organic Models, Modular Kits, Props, Vehicles, Weapons, Creatures, Architectural Elements, CAD Parts, C4D Scenes

Video: Short Form, Long Form, Cutscenes, Loops, Motion Graphics, Explainers, Product Demos, Cinematic Sequences

Interactive: Game Environments, VR/AR Assets, UI/UX Systems, Simulation Modules, WebGL/Canvas Elements



------------------------------------------------------------

STYLE DIMENSIONS

Rendering Styles: Photorealism, Cel‑Shading, Painterly, Sketch, Line Art, Pixel Art, Vector Flat, Toon, Vaporwave, Synthwave, Noir, Cyberpunk, Steampunk, Dieselpunk, Rococo, Baroque, Brutalist, Minimalist, Maximalist, Surrealist, Impressionist, Expressionist, Gothic, Art Deco, Art Nouveau, Ukiyo‑e, Manga (Shonen, Shojo, Seinen, Josei), Anime (Classic, Modern, Ghibli‑style, Trigger‑style), Comic Book (Western, Indie), Retro 80s/90s, Y2K, Fantasy (High, Dark, Urban), Sci‑Fi (Hard, Soft, Retro‑futurist), Horror (Psychological, Gore, Cosmic), Mythic/Ceremonial, Ethereal/Dreamlike, Flat Design, Isometric, Low Poly, High Poly, Clay Render, Wireframe, Blueprint/Technical



Genre/Aesthetic Tags: Heroic, Villainous, Romantic, Tragic, Comedic, Melancholic, Whimsical, Stoic, Gritty, Elegant, Chaotic, Sacred, Industrial, Organic, Synthetic, Celestial, Infernal, Post‑Apocalyptic, Utopian, Dystopian, Historical, Futuristic, Timeless, Technological, Pastoral, Musical, Theatrical, Naval Adventure, Golden Age Hollywood, Classic Americana, Vintage Holiday



Time Periods: Prehistoric, Ancient, Medieval, Renaissance, Victorian, Edwardian, Industrial Revolution, WWI/WWII, 1950s–1990s, Near Future, Far Future, Timeless/Mythic



Reference Libraries: Curated sets per time period and aesthetic, schema‑based tagging, used for grounding ControlNet, IP‑Adapter, palette enforcement.



------------------------------------------------------------

WORKFLOW ARCHITECTURE

Layers:

1\. Foundation Layer – Character, Environment, Style Guide

2\. Planning Layer – Job schema, helper pass selection

3\. Generation Layer – SDXL, Refiner, ControlNet, IP‑Adapter

4\. Enhancement Layer – Dual SR, semantic downrezzing

5\. Assembly Layer – Video stitching, transitions, layout

6\. Validation Layer – Quality gates, drift detection, anatomy checks

7\. Packaging Layer – Asset bundling, metadata, previews

8\. Archive Layer – Compressed lineage archive with snapshots and rejection reasons



Feedback Loops:

\- Validate at each layer

\- Auto‑reject if consistency < threshold

\- Retry with alternate helper passes

\- Store lineage metadata and evaluation scores

\- Escalate constraints if stuck

\- Archive rejected outputs for AI self‑study



Dependency Graph Execution:

\- Ordered execution with dependency tracking

\- Parallel execution where possible

\- Circular dependency detection

\- Regeneration of failed nodes without full rebuild



------------------------------------------------------------

EVALUATION SYSTEM

\- Multi‑Pass Evaluation: default 3–5 passes, configurable 1–10

\- Metrics: Sharpness, Anatomy, Prompt Alignment, Consistency, Color Fidelity

\- Schema‑based scoring per output type

\- Auto‑select winner with LLM explanation

\- Learn from user overrides

\- Escalate if stuck after N iterations



------------------------------------------------------------

PRECISION CONTROL SYSTEMS

1\. Layer‑Based Composition

2\. Mask‑Driven Regional Control

3\. Embedding Fingerprinting \& Drift Detection

4\. Iterative Inpainting Protocol

5\. Multi‑Reference Blending

6\. Semantic Segmentation Lock

7\. Color Palette Enforcement

8\. Geometry \& Perspective Validation

9\. Temporal Coherence Protocol

10\. Quality Gate System

11\. Version Control \& Branching



------------------------------------------------------------

COMPRESSED LINEAGE ARCHIVE

\- Stores snapshots of every generation pass

\- Includes rejected outputs, reasons, evaluation scores, helper passes, prompt context, timestamp, model version

\- Uses compression and delta encoding

\- Enables AI self‑study and user transparency

\- Supports rollback, branching, merge strategies



------------------------------------------------------------

INTEGRATION STRATEGIES

Languages: Python (orchestration, CLI, API), Rust (performance modules, validators), C++ (system‑level control, render hooks)

Libraries: OpenGL/WebGPU, FFmpeg, Trimesh/Open3D, PyTorch + Diffusers, Git‑style versioning, TUI libraries

CLI UX: Pop‑up previews, AI+user discussion mode, keyboard shortcuts, scrollback, live reload, branch explorer, reference viewer, undo/redo



------------------------------------------------------------

MODULES

forge\_agent – Planner, job schema, web search

forge\_diffusion – SDXL, Refiner, ControlNet, IP‑Adapter

forge\_sr – Dual SR runners, comparison

forge\_video – Img2Vid wrapper

forge\_semantic – Downrez ladder

forge\_packaging – Zip bundler, metadata, previews

forge\_monitor – Thermal sensors, logs

forge\_validator – Anatomy, perspective, color checks

forge\_versioning – Git‑style branching

forge\_cli – Terminal interface, preview popups

forge\_lineage – Compressed lineage archive, rejection snapshots



------------------------------------------------------------

BUILDING NATIVE COMPONENTS (C++ + Rust via maturin)

Quick Start:

\- C++: scripts/build\_cpp.ps1 -Release

\- Rust PyO3: pip install maturin, then scripts/build\_rust.ps1 -Release

\- Both: scripts/build\_all.ps1 -Release



Artifacts:

\- C++ DLL/SO/DYLIB under vaultmind\_forge/native/cpp/validator/build

\- Rust Python extension installed into current environment by maturin develop



Advanced Options:

\- Ninja generator, ccache/sccache, vcpkg for deps

\- maturin build --release for wheels, auditwheel/delocate for packaging

\- Use uv/rye or mamba/conda for reproducible envs

\- WSL2 for GNU toolchain, CUDA/ROCm for GPU

\- SIMD/Parallel: AVX2/AVX512, OpenMP/TBB, rayon

\- GPU backends: Vulkan (Kompute), CUDA, OpenCL

\- IO: FFmpeg, OpenImageIO

\- Pre‑commit hooks, CI with GitHub Actions, vcpkg manifest mode

\- Emulators/VMs: QEMU/UTM, Docker for cross‑compiling



Troubleshooting:

\- Ensure maturin develop ran in active env

\- Copy DLL next to forge\_validator/backends.py or add folder to PATH



------------------------------------------------------------

PROPOSED FOLDER STRUCTURE

vaultmind\_forge/

&nbsp; forge\_agent/

&nbsp; forge\_diffusion/

&nbsp; forge\_sr/

&nbsp; forge\_video/

&nbsp; forge\_semantic/

&nbsp; forge\_packaging/

&nbsp; forge\_monitor/

&nbsp; forge\_validator/

&nbsp; forge\_versioning/

&nbsp; forge\_cli/

&nbsp; forge\_lineage/

&nbsp; assets/

&nbsp;   images/

&nbsp;   meshes/

&nbsp;   videos/

&nbsp;   packages/

&nbsp; references/

&nbsp;   style\_guides/

&nbsp;   palettes/

&nbsp;   embeddings/

&nbsp;   time\_periods/

&nbsp;   aesthetics/

&nbsp; lineage\_logs/

&nbsp;   accepted/

&nbsp;   rejected/

&nbsp;   archives/

&nbsp; config/

&nbsp;   runtime/

&nbsp;   presets/

&nbsp;   schemas/

&nbsp; native/

&nbsp;   cpp/

&nbsp;     validator/

&nbsp;       build/

&nbsp;   rust/

&nbsp;     validator/

&nbsp;       build/

&nbsp; scripts/

&nbsp;   build\_cpp.ps1

&nbsp;   build\_rust.ps1

&nbsp;   build\_all.ps1

