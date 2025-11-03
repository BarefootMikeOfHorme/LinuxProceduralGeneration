"""
VaultMind Forge - Job Schemas
Pydantic models for job configuration and validation
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class OutputType(str, Enum):
    """Supported output types for asset generation"""
    # 2D Assets
    CHARACTER_2D = "character_2d"
    CONCEPT_ART = "concept_art"
    STORYBOARD = "storyboard"
    UI_MOCKUP = "ui_mockup"
    ICON = "icon"
    TEXTURE = "texture"
    SPRITE = "sprite"

    # 3D Assets
    CHARACTER_3D = "character_3d"
    ENVIRONMENT = "environment"
    PROP = "prop"
    VEHICLE = "vehicle"

    # Video/Animation
    VIDEO_CLIP = "video_clip"
    ANIMATION = "animation"
    CINEMATIC = "cinematic"

    # Technical
    TECHNICAL_DIAGRAM = "technical_diagram"
    BLUEPRINT = "blueprint"
    CAD_MODEL = "cad_model"


class RenderStyle(str, Enum):
    """Rendering style presets"""
    PHOTOREALISTIC = "photorealistic"
    CEL_SHADED = "cel_shaded"
    ANIME = "anime"
    MANGA = "manga"
    PAINTERLY = "painterly"
    SKETCH = "sketch"
    LINE_ART = "line_art"
    PIXEL_ART = "pixel_art"
    LOW_POLY = "low_poly"
    ISOMETRIC = "isometric"
    VAPORWAVE = "vaporwave"
    CYBERPUNK = "cyberpunk"
    FANTASY = "fantasy"
    SCI_FI = "sci_fi"
    NOIR = "noir"


class QualityPreset(str, Enum):
    """Quality presets for generation"""
    DRAFT = "draft"          # Fast, lower quality
    STANDARD = "standard"    # Balanced
    HIGH = "high"           # Higher quality, slower
    PRODUCTION = "production"  # Maximum quality


class ColorSpace(str, Enum):
    """Color space for output"""
    SRGB = "srgb"
    LINEAR = "linear"
    ACES = "aces"
    REC709 = "rec709"


class AspectRatio(BaseModel):
    """Aspect ratio specification"""
    width: int = Field(gt=0, description="Width in pixels")
    height: int = Field(gt=0, description="Height in pixels")

    @property
    def ratio(self) -> float:
        """Get aspect ratio as float"""
        return self.width / self.height

    def __str__(self) -> str:
        return f"{self.width}x{self.height}"


class StyleConstraints(BaseModel):
    """Style constraints for generation"""
    color_palette: Optional[List[str]] = Field(
        default=None,
        description="List of hex color codes for palette enforcement"
    )
    color_temperature: Optional[Literal["warm", "cool", "neutral"]] = None
    contrast_level: Optional[Literal["low", "medium", "high"]] = "medium"
    saturation_level: Optional[Literal["low", "medium", "high"]] = "medium"
    lighting_style: Optional[Literal["soft", "hard", "dramatic", "flat"]] = None
    time_of_day: Optional[Literal["dawn", "day", "dusk", "night"]] = None
    weather: Optional[Literal["clear", "cloudy", "rainy", "foggy", "stormy"]] = None


class ValidationRequirements(BaseModel):
    """Validation requirements for output"""
    min_sharpness_score: float = Field(default=0.7, ge=0.0, le=1.0)
    min_anatomy_score: float = Field(default=0.7, ge=0.0, le=1.0)
    min_prompt_alignment: float = Field(default=0.7, ge=0.0, le=1.0)
    min_consistency_score: float = Field(default=0.7, ge=0.0, le=1.0)
    min_color_fidelity: float = Field(default=0.7, ge=0.0, le=1.0)

    required_elements: Optional[List[str]] = Field(
        default=None,
        description="Elements that must be present in output"
    )
    forbidden_elements: Optional[List[str]] = Field(
        default=None,
        description="Elements that must not be present in output"
    )


class Reference(BaseModel):
    """Reference material for generation"""
    path: str = Field(description="Path to reference file")
    type: Literal["style", "color", "composition", "anatomy", "lighting"] = "style"
    weight: float = Field(default=1.0, ge=0.0, le=2.0, description="Influence weight")
    description: Optional[str] = None


class LineageConfig(BaseModel):
    """Lineage tracking configuration"""
    lineage_id: Optional[str] = None
    job_id: str = Field(description="Unique job identifier")
    branch: str = Field(default="main", description="Lineage branch name")
    parent: Optional[str] = Field(default=None, description="Parent lineage ID")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GenerationParams(BaseModel):
    """Low-level generation parameters"""
    # Diffusion params
    steps: int = Field(default=30, ge=1, le=150, description="Number of diffusion steps")
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0, description="CFG scale")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")

    # Image params
    width: int = Field(default=512, ge=64, le=2048)
    height: int = Field(default=512, ge=64, le=2048)

    # Advanced
    negative_prompt: Optional[str] = None
    clip_skip: int = Field(default=0, ge=0, le=12)
    sampler: str = Field(default="euler_a")


class JobConfig(BaseModel):
    """
    Complete job configuration for asset generation.

    This is the master schema that defines all parameters for a generation job.
    """
    # Identification
    id: str = Field(description="Unique job ID")
    name: str = Field(description="Human-readable job name")
    description: Optional[str] = None

    # Output specification
    output_type: OutputType = Field(description="Type of asset to generate")
    render_style: RenderStyle = Field(description="Rendering style")
    quality_preset: QualityPreset = Field(default=QualityPreset.STANDARD)

    # Dimensions
    aspect_ratio: AspectRatio = Field(
        default=AspectRatio(width=512, height=512)
    )
    target_resolution: Optional[AspectRatio] = Field(
        default=None,
        description="Final resolution after upscaling"
    )

    # Prompts
    main_prompt: str = Field(description="Primary generation prompt")
    negative_prompt: Optional[str] = Field(default=None)
    style_tags: List[str] = Field(
        default_factory=list,
        description="Additional style tags"
    )

    # Constraints
    style_constraints: Optional[StyleConstraints] = None
    validation_requirements: ValidationRequirements = Field(
        default_factory=ValidationRequirements
    )

    # References
    references: List[Reference] = Field(
        default_factory=list,
        description="Reference materials"
    )

    # Generation
    generation_params: GenerationParams = Field(
        default_factory=GenerationParams
    )

    # Multi-pass
    multi_pass_enabled: bool = Field(
        default=False,
        description="Enable multi-pass generation with selection"
    )
    num_passes: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of passes if multi-pass enabled"
    )

    # Lineage
    lineage: LineageConfig = Field(description="Lineage tracking config")

    # Output
    output_dir: str = Field(default="./output")
    output_format: Literal["png", "jpg", "webp", "exr"] = "png"
    color_space: ColorSpace = Field(default=ColorSpace.SRGB)

    # Packaging
    package_output: bool = Field(
        default=True,
        description="Create packaged archive with metadata"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    @field_validator("style_tags")
    @classmethod
    def validate_style_tags(cls, v):
        """Ensure style tags are unique and lowercase"""
        return list(set(tag.lower().strip() for tag in v))

    @field_validator("num_passes")
    @classmethod
    def validate_passes(cls, v, info):
        """Ensure num_passes is valid when multi-pass is enabled"""
        if info.data.get("multi_pass_enabled") and v < 2:
            raise ValueError("num_passes must be >= 2 when multi_pass_enabled is True")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> JobConfig:
        """Create JobConfig from dictionary"""
        return cls.model_validate(data)


class JobTemplate(BaseModel):
    """
    Reusable job template for common generation patterns.
    """
    name: str = Field(description="Template name")
    description: str = Field(description="Template description")
    output_type: OutputType
    render_style: RenderStyle
    quality_preset: QualityPreset = QualityPreset.STANDARD

    # Default values
    default_aspect_ratio: AspectRatio = Field(
        default=AspectRatio(width=512, height=512)
    )
    default_style_tags: List[str] = Field(default_factory=list)
    default_style_constraints: Optional[StyleConstraints] = None
    default_validation_requirements: ValidationRequirements = Field(
        default_factory=ValidationRequirements
    )
    default_generation_params: GenerationParams = Field(
        default_factory=GenerationParams
    )

    def create_job(
        self,
        job_id: str,
        job_name: str,
        main_prompt: str,
        **overrides
    ) -> JobConfig:
        """
        Create a JobConfig from this template.

        Args:
            job_id: Unique job identifier
            job_name: Human-readable name
            main_prompt: Generation prompt
            **overrides: Any fields to override from template

        Returns:
            JobConfig instance
        """
        config_data = {
            "id": job_id,
            "name": job_name,
            "main_prompt": main_prompt,
            "output_type": self.output_type,
            "render_style": self.render_style,
            "quality_preset": self.quality_preset,
            "aspect_ratio": self.default_aspect_ratio,
            "style_tags": self.default_style_tags.copy(),
            "style_constraints": self.default_style_constraints,
            "validation_requirements": self.default_validation_requirements,
            "generation_params": self.default_generation_params,
            "lineage": LineageConfig(job_id=job_id),
            **overrides
        }

        return JobConfig.model_validate(config_data)


# Predefined Templates
ANIME_CHARACTER_TEMPLATE = JobTemplate(
    name="anime_character",
    description="Anime-style character portrait",
    output_type=OutputType.CHARACTER_2D,
    render_style=RenderStyle.ANIME,
    default_aspect_ratio=AspectRatio(width=512, height=768),
    default_style_tags=["anime", "character portrait", "clean lines"],
    default_validation_requirements=ValidationRequirements(
        min_anatomy_score=0.75,
        min_sharpness_score=0.80
    ),
)

CONCEPT_ART_TEMPLATE = JobTemplate(
    name="concept_art",
    description="Game concept art",
    output_type=OutputType.CONCEPT_ART,
    render_style=RenderStyle.PAINTERLY,
    quality_preset=QualityPreset.HIGH,
    default_aspect_ratio=AspectRatio(width=1024, height=768),
    default_style_tags=["concept art", "detailed", "professional"],
)

PIXEL_ART_TEMPLATE = JobTemplate(
    name="pixel_art",
    description="Retro pixel art sprite",
    output_type=OutputType.SPRITE,
    render_style=RenderStyle.PIXEL_ART,
    default_aspect_ratio=AspectRatio(width=64, height=64),
    default_style_tags=["pixel art", "retro", "8-bit"],
    default_generation_params=GenerationParams(
        steps=20,
        width=64,
        height=64,
    ),
)

ENVIRONMENT_TEMPLATE = JobTemplate(
    name="environment",
    description="3D environment concept",
    output_type=OutputType.ENVIRONMENT,
    render_style=RenderStyle.PHOTOREALISTIC,
    quality_preset=QualityPreset.PRODUCTION,
    default_aspect_ratio=AspectRatio(width=1920, height=1080),
    default_style_tags=["environment", "detailed", "atmospheric"],
)
