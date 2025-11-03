# forge_agent

**Intelligent Job Planning and Schema Management for AI Asset Generation**

## Overview

The `forge_agent` module provides comprehensive job planning, schema validation, and style management for VaultMind Forge. It features Pydantic-based schemas, intelligent resource estimation, and curated style presets.

## Features

- **Pydantic Schemas**: Type-safe job configurations with validation
- **Intelligent Planner**: Automatic helper pass selection and resource estimation
- **Style Presets**: Curated collection of 15+ professional style presets
- **Template System**: Reusable templates for common patterns
- **Batch Jobs**: Create variations from base configurations
- **Resource Estimation**: Predict generation time and memory usage

## Quick Start

### Creating Jobs

```python
from vaultmind_forge.forge_agent import JobPlanner, OutputType, RenderStyle

planner = JobPlanner()

# Simple job creation
job = planner.create_simple_job(
    name="Hero Character",
    prompt="heroic warrior with glowing sword, detailed armor",
    output_type=OutputType.CHARACTER_2D,
    render_style=RenderStyle.ANIME,
    width=512,
    height=768,
    multi_pass=True,
    num_passes=3
)

# Generate execution plan
plan = planner.create_plan(job)
print(f"Est. time: {plan.estimated_time_minutes:.1f} min")
print(f"Est. memory: {plan.estimated_memory_gb:.1f} GB")
print(f"Helpers: {[h.value for h in plan.recommended_helpers]}")
```

### Using Templates

```python
from vaultmind_forge.forge_agent import ANIME_CHARACTER_TEMPLATE

# Create job from template
job = ANIME_CHARACTER_TEMPLATE.create_job(
    job_id="job_001",
    job_name="Magical Girl Character",
    main_prompt="magical girl with staff, flowing ribbons, sparkles"
)
```

### Style Presets

```python
from vaultmind_forge.forge_agent import get_style_preset, enhance_prompt_with_style

# Get style preset
style = get_style_preset("classic_anime")
print(f"Guidance: {style.recommended_guidance}")
print(f"Keywords: {style.positive_keywords}")

# Enhance prompt with style
prompts = enhance_prompt_with_style(
    base_prompt="warrior character",
    style_name="cyberpunk"
)
print(prompts["positive"])   # Enhanced with cyberpunk keywords
print(prompts["negative"])   # Cyberpunk negative keywords
```

### Batch Job Creation

```python
# Create variations
variations = [
    {"render_style": RenderStyle.ANIME},
    {"render_style": RenderStyle.CEL_SHADED},
    {"render_style": RenderStyle.PAINTERLY},
]

batch_jobs = planner.create_batch_jobs(base_job, variations)
# Creates 3 jobs with different rendering styles
```

## Available Style Presets

### Anime/Manga
- `classic_anime` - Traditional anime with clean lines
- `modern_anime` - Contemporary anime with lighting effects
- `manga_style` - Black and white manga

### Realistic
- `photorealistic` - Photographic realism
- `cinematic` - Film-quality rendering

### Artistic
- `painterly` - Traditional painting style
- `concept_art` - Professional concept art
- `watercolor` - Soft watercolor painting

### Stylized
- `cel_shaded` - Flat shading with outlines
- `low_poly` - Geometric 3D style
- `pixel_art` - Retro pixel art
- `isometric` - Isometric game art

### Sci-Fi
- `cyberpunk` - Neon-lit cyberpunk
- `vaporwave` - Retro vaporwave aesthetic

## Job Schema

Complete schema with all options:

```python
from vaultmind_forge.forge_agent import (
    JobConfig,
    OutputType,
    RenderStyle,
    QualityPreset,
    AspectRatio,
    StyleConstraints,
    ValidationRequirements,
    GenerationParams,
)

job = JobConfig(
    id="job_001",
    name="Character Portrait",
    main_prompt="detailed character portrait",
    output_type=OutputType.CHARACTER_2D,
    render_style=RenderStyle.ANIME,
    quality_preset=QualityPreset.HIGH,
    aspect_ratio=AspectRatio(width=512, height=768),

    # Style constraints
    style_constraints=StyleConstraints(
        color_palette=["#FF6B6B", "#4ECDC4", "#45B7D1"],
        color_temperature="warm",
        lighting_style="soft"
    ),

    # Validation requirements
    validation_requirements=ValidationRequirements(
        min_sharpness_score=0.75,
        min_anatomy_score=0.80
    ),

    # Generation params
    generation_params=GenerationParams(
        steps=35,
        guidance_scale=7.5,
        seed=42
    ),

    # Multi-pass
    multi_pass_enabled=True,
    num_passes=5,
)
```

## API Reference

### JobPlanner

**`create_simple_job(...) -> JobConfig`**

Create job with minimal parameters.

**`create_plan(job_config: JobConfig) -> GenerationPlan`**

Generate execution plan with recommendations.

**`create_batch_jobs(base_config, variations) -> List[JobConfig]`**

Create batch jobs from variations.

### GenerationPlan

Result of `create_plan()` containing:
- `job_config`: Complete job configuration
- `recommended_helpers`: List of recommended helper passes
- `estimated_time_minutes`: Time estimate
- `estimated_memory_gb`: Memory estimate
- `optimization_notes`: Optimization suggestions
- `warnings`: Potential issues

### Enums

**OutputType**: CHARACTER_2D, CONCEPT_ART, ENVIRONMENT, etc.

**RenderStyle**: ANIME, PHOTOREALISTIC, PAINTERLY, etc.

**QualityPreset**: DRAFT, STANDARD, HIGH, PRODUCTION

**HelperPass**: DEPTH_MAP, CANNY_EDGE, POSE_SKELETON, etc.

## Integration Example

```python
from vaultmind_forge.forge_agent import JobPlanner, OutputType, RenderStyle
from vaultmind_forge.forge_monitor import SystemMonitor

planner = JobPlanner()
monitor = SystemMonitor()

# Create and plan job
job = planner.create_simple_job(
    name="Concept Art",
    prompt="futuristic city skyline at sunset",
    output_type=OutputType.ENVIRONMENT,
    render_style=RenderStyle.CONCEPT_ART
)

plan = planner.create_plan(job)

# Check if resources are sufficient
snapshot = monitor.capture_snapshot()
if snapshot.memory_available_gb < plan.estimated_memory_gb:
    print(f"⚠️ Insufficient memory: need {plan.estimated_memory_gb}GB")
else:
    print(f"✓ Ready to generate (est. {plan.estimated_time_minutes} min)")
    # Proceed with generation...
```

## Status

**Version:** 1.0.0
**Status:** Production-Ready
**Last Updated:** 2025-11-03

---

**Part of VaultMind Forge** - AI-powered asset generation with complete lineage tracking
