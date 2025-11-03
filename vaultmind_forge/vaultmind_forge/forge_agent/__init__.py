"""
VaultMind Forge - Agent Module

Intelligent job planning, schema management, and style presets for AI asset generation.

Features:
- Pydantic-based job schemas with validation
- Intelligent job planner with resource estimation
- Curated style presets with prompt templates
- Helper pass recommendations
- Batch job creation
- Template system for common patterns

Example:
    from vaultmind_forge.forge_agent import JobPlanner, OutputType, RenderStyle

    # Create simple job
    planner = JobPlanner()
    job = planner.create_simple_job(
        name="Hero Character",
        prompt="heroic warrior with glowing sword",
        output_type=OutputType.CHARACTER_2D,
        render_style=RenderStyle.ANIME,
        multi_pass=True
    )

    # Generate plan with recommendations
    plan = planner.create_plan(job)
    print(f"Estimated time: {plan.estimated_time_minutes} minutes")
    print(f"Recommended helpers: {plan.recommended_helpers}")
"""

from __future__ import annotations

from .schemas import (
    JobConfig,
    JobTemplate,
    OutputType,
    RenderStyle,
    QualityPreset,
    ColorSpace,
    AspectRatio,
    StyleConstraints,
    ValidationRequirements,
    GenerationParams,
    LineageConfig,
    Reference,
    # Predefined templates
    ANIME_CHARACTER_TEMPLATE,
    CONCEPT_ART_TEMPLATE,
    PIXEL_ART_TEMPLATE,
    ENVIRONMENT_TEMPLATE,
)

from .planner import (
    JobPlanner,
    GenerationPlan,
    HelperPass,
)

from .styles import (
    StylePreset,
    get_style_preset,
    list_presets_by_style,
    enhance_prompt_with_style,
    # Style collections
    ANIME_STYLES,
    REALISTIC_STYLES,
    ARTISTIC_STYLES,
    STYLIZED_STYLES,
    SCIFI_STYLES,
    ALL_STYLES,
)

__all__ = [
    # Core schemas
    "JobConfig",
    "JobTemplate",
    # Enums
    "OutputType",
    "RenderStyle",
    "QualityPreset",
    "ColorSpace",
    # Schema components
    "AspectRatio",
    "StyleConstraints",
    "ValidationRequirements",
    "GenerationParams",
    "LineageConfig",
    "Reference",
    # Templates
    "ANIME_CHARACTER_TEMPLATE",
    "CONCEPT_ART_TEMPLATE",
    "PIXEL_ART_TEMPLATE",
    "ENVIRONMENT_TEMPLATE",
    # Planner
    "JobPlanner",
    "GenerationPlan",
    "HelperPass",
    # Styles
    "StylePreset",
    "get_style_preset",
    "list_presets_by_style",
    "enhance_prompt_with_style",
    "ANIME_STYLES",
    "REALISTIC_STYLES",
    "ARTISTIC_STYLES",
    "STYLIZED_STYLES",
    "SCIFI_STYLES",
    "ALL_STYLES",
]

__version__ = "1.0.0"
