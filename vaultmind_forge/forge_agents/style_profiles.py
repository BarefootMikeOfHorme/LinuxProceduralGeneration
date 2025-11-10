"""
VaultMind Forge - Style & Aesthetic Profiles
Research-backed generation parameters and quality standards for different art styles

Parameters based on 2024 industry best practices from:
- Stable Diffusion community recommendations
- Professional AI art generation workflows
- Game development pipelines
- Production studios

Each profile includes:
- Generation parameters (steps, CFG, sampler, etc.)
- Quality thresholds (what's acceptable for this style)
- Prompt enhancement keywords
- Material/texture specifications
- User-tunable parameter ranges
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional


class StyleCategory(Enum):
    """Style categories"""
    REALISTIC = "realistic"
    STYLIZED = "stylized"
    ANIME = "anime"
    RETRO = "retro"
    ATMOSPHERIC = "atmospheric"
    PAINTERLY = "painterly"


@dataclass
class ParameterRange:
    """User-tunable parameter range"""
    default: float
    min: float
    max: float
    description: str

    def validate(self, value: float) -> float:
        """Validate and clamp value to range"""
        return max(self.min, min(self.max, value))


@dataclass
class StyleProfile:
    """
    Complete style/aesthetic profile for context-aware generation & validation.

    All parameters are research-backed from 2024 industry best practices.
    """

    # === Identification ===
    name: str
    category: StyleCategory
    description: str
    tags: List[str]

    # === Quality Standards (for Quality Guardian) ===
    quality_thresholds: Dict[str, float]
    """
    Quality metric thresholds (0.0-1.0).
    Different styles have different acceptable quality ranges.

    Common metrics:
    - sharpness: Image sharpness (0.0-1.0)
    - anatomy: Anatomical accuracy for characters (0.0-1.0)
    - color_fidelity: Color accuracy (0.0-1.0)
    - contrast: Contrast level (0.0-1.0)
    - noise_level: Noise/grain (lower is less noisy)
    - min_overall_quality: Minimum acceptable overall score
    """

    priority_metrics: List[str]
    """Metrics most important for this style (weighted higher)"""

    acceptable_artifacts: List[str]
    """Artifacts that are OK/expected for this style"""

    # === Generation Parameters (for Parameter Optimizer) ===
    # Based on 2024 Stable Diffusion best practices
    generation_params: Dict[str, Any]
    """
    Recommended generation parameters.

    Key parameters:
    - steps: Sampling steps (20-50 typical)
    - cfg_scale: Classifier-Free Guidance (4-15 typical)
    - sampler: Sampling method (DPM++ 2M Karras, Euler a, etc.)
    - clip_skip: CLIP layers to skip (1-2 typical)
    - enable_hires_fix: High-res fix pass (True/False)
    - denoising_strength: Denoising strength (0.0-1.0)
    """

    tunable_params: Dict[str, ParameterRange]
    """User/AI adjustable parameter ranges"""

    negative_prompt_defaults: str
    """Default negative prompt for this style"""

    lora_recommendations: List[str]
    """Recommended LoRA models"""

    # === Prompt Enhancement (for Prompt Refiner) ===
    style_keywords: List[str]
    """Keywords that define this style"""

    quality_keywords: List[str]
    """Keywords for quality enhancement"""

    avoid_keywords: List[str]
    """Keywords to avoid (anti-style)"""

    # === Material/Technical (for Material Suggestor) ===
    preferred_pbr_ranges: Dict[str, Tuple[float, float]]
    """PBR parameter ranges (roughness, metallic, etc.)"""

    shader_preferences: List[str]
    """Preferred shader types"""

    texture_requirements: Dict[str, Any]
    """Texture specifications"""


# ==============================================================================
# PHOTOREALISTIC PROFILE
# Research: OpenArt, FlyWithAI, Stable Diffusion Art community (2024)
# ==============================================================================

PHOTOREALISTIC_PROFILE = StyleProfile(
    # Identification
    name="Photorealistic",
    category=StyleCategory.REALISTIC,
    description="Professional photorealistic images mimicking real photography. "
                "High detail, accurate anatomy, natural lighting.",
    tags=["photorealistic", "realistic", "photoreal", "photography", "lifelike", "real"],

    # Quality Standards
    quality_thresholds={
        "sharpness": 0.80,              # HIGH - crisp details essential
        "anatomy": 0.85,                # HIGH - realistic proportions critical
        "color_fidelity": 0.75,         # MEDIUM-HIGH - natural colors
        "prompt_alignment": 0.80,       # HIGH - should match exactly
        "noise_level": 0.15,            # LOW - minimal grain acceptable
        "contrast": 0.60,               # MEDIUM - natural contrast
        "brightness": 0.45,             # MEDIUM - natural lighting
        "min_overall_quality": 0.78     # 78% overall minimum
    },

    priority_metrics=["sharpness", "anatomy", "color_fidelity"],

    acceptable_artifacts=[
        "natural_grain",         # Film grain OK in moderation
        "lens_effects",          # Bokeh, lens flare acceptable
        "subtle_noise",          # Slight noise like real cameras
    ],

    # Generation Parameters (Research-backed 2024 best practices)
    generation_params={
        "steps": 30,                    # 20-30 optimal per research
        "cfg_scale": 7.5,               # 7-10 recommended for photorealism
        "sampler": "DPM++ 2M Karras",   # Best balance quality/speed
        "clip_skip": 1,                 # No skip for realism
        "enable_hires_fix": True,       # Always use for quality
        "denoising_strength": 0.4,      # Moderate denoising
        "scheduler": "karras",          # Karras scheduler recommended
    },

    # User-tunable ranges
    tunable_params={
        "steps": ParameterRange(
            default=30,
            min=20,
            max=50,
            description="More steps = more detail but slower"
        ),
        "cfg_scale": ParameterRange(
            default=7.5,
            min=5.0,
            max=12.0,
            description="Higher = closer to prompt, but artifacts >12"
        ),
        "denoising_strength": ParameterRange(
            default=0.4,
            min=0.2,
            max=0.7,
            description="Lower = preserve original, higher = more changes"
        ),
    },

    negative_prompt_defaults=(
        "cartoon, anime, painting, drawing, illustration, 3d render, cgi, "
        "unrealistic, fake, plastic, doll, low quality, blurry, grainy, "
        "bad anatomy, deformed, disfigured"
    ),

    lora_recommendations=["realistic_vision", "detail_enhancer", "add_detail"],

    # Prompt Enhancement
    style_keywords=[
        "photorealistic", "8k uhd", "dslr", "sharp focus",
        "highly detailed", "professional photography",
        "natural lighting", "raw photo", "film grain"
    ],

    quality_keywords=[
        "high resolution", "detailed", "crisp", "clear",
        "physically-based rendering", "ray tracing",
        "depth of field", "professional"
    ],

    avoid_keywords=[
        "painted", "illustrated", "stylized", "cartoon",
        "anime", "drawn", "rendered", "cgi"
    ],

    # Material Properties
    preferred_pbr_ranges={
        "roughness": (0.3, 0.7),        # Natural materials range
        "metallic": (0.0, 0.2),         # Most things not metal
        "specular": (0.4, 0.6),         # Realistic specularity
    },

    shader_preferences=["pbr_standard", "subsurface_scattering", "clearcoat"],

    texture_requirements={
        "min_resolution": 2048,
        "preferred_resolution": 4096,
        "format": "png",
        "color_space": "sRGB",
        "bit_depth": 8,
        "include_maps": ["albedo", "normal", "roughness", "ao", "displacement"]
    }
)


# ==============================================================================
# ANIME/MANGA PROFILE
# Research: Stable Diffusion community, Civitai anime models (2024)
# ==============================================================================

ANIME_PROFILE = StyleProfile(
    # Identification
    name="Anime",
    category=StyleCategory.ANIME,
    description="Japanese anime/manga art style. Clean linework, cel-shading, "
                "vibrant colors, stylized proportions.",
    tags=["anime", "manga", "japanese animation", "cel-shaded", "anime style"],

    # Quality Standards (Different from photorealistic!)
    quality_thresholds={
        "sharpness": 0.85,              # VERY HIGH - clean lines critical
        "anatomy": 0.60,                # LOWER - stylized proportions OK
        "color_fidelity": 0.70,         # MEDIUM - vibrant expected
        "prompt_alignment": 0.75,       # MEDIUM-HIGH
        "line_quality": 0.80,           # HIGH - clean linework essential
        "color_saturation": 0.70,       # HIGH - vibrant anime colors
        "contrast": 0.65,               # MEDIUM-HIGH
        "min_overall_quality": 0.68     # 68% overall (more lenient)
    },

    priority_metrics=["sharpness", "line_quality", "color_saturation"],

    acceptable_artifacts=[
        "cel_shading",           # Expected style
        "bold_outlines",         # Part of aesthetic
        "simplified_details",    # Stylization
        "flat_colors",          # Anime style
    ],

    # Generation Parameters (Anime-specific best practices 2024)
    generation_params={
        "steps": 28,                    # 20-30 optimal for anime
        "cfg_scale": 7.5,               # 7-8 good for anime (research)
        "sampler": "Euler a",           # Better for anime than DPM++
        "clip_skip": 2,                 # CRITICAL: Skip 2 for anime models!
        "enable_hires_fix": True,       # Clean lines need it
        "denoising_strength": 0.5,      # Moderate
        "scheduler": "normal",          # Normal scheduler for anime
    },

    tunable_params={
        "steps": ParameterRange(
            default=28,
            min=20,
            max=40,
            description="Anime needs fewer steps than realistic"
        ),
        "cfg_scale": ParameterRange(
            default=7.5,
            min=6.0,
            max=11.0,
            description="Too high causes over-saturation in anime"
        ),
        "clip_skip": ParameterRange(
            default=2,
            min=1,
            max=2,
            description="Always use 2 for anime models!"
        ),
    },

    negative_prompt_defaults=(
        "realistic, photorealistic, 3d, photograph, "
        "western cartoon, blur, sketch, bad anatomy, "
        "lowres, bad hands, text, error, missing fingers, "
        "extra digit, fewer digits, cropped, worst quality, low quality"
    ),

    lora_recommendations=["anime_style", "detail_tweaker", "add_sharpness"],

    # Prompt Enhancement
    style_keywords=[
        "anime", "anime style", "manga style", "cel-shaded",
        "clean linework", "vibrant colors", "anime art",
        "by makoto shinkai", "ghibli style", "anime aesthetic"
    ],

    quality_keywords=[
        "highly detailed", "best quality", "masterpiece",
        "clean lines", "vibrant", "colorful", "sharp",
        "anime coloring", "detailed eyes"
    ],

    avoid_keywords=[
        "realistic", "photograph", "3d render", "western style",
        "blurry", "ugly", "bad anatomy"
    ],

    # Material Properties
    preferred_pbr_ranges={
        "roughness": (0.6, 0.9),        # Matte cel-shaded look
        "metallic": (0.0, 0.1),         # Very low metallic
        "specular": (0.3, 0.5),         # Subtle highlights
    },

    shader_preferences=["cel_shader", "toon_shader", "flat_shading", "outline_shader"],

    texture_requirements={
        "min_resolution": 1024,
        "preferred_resolution": 2048,
        "format": "png",
        "color_space": "sRGB",
        "bit_depth": 8,
        "include_maps": ["albedo", "cel_ramp", "outline"]
    }
)


# ==============================================================================
# FANTASY/GAME ART PROFILE
# Research: Game dev studios, Blizzard/Riot style guides, CG Spectrum (2024)
# ==============================================================================

FANTASY_GAME_PROFILE = StyleProfile(
    # Identification
    name="Fantasy Game Art",
    category=StyleCategory.STYLIZED,
    description="Stylized game asset art (WoW, LoL, Overwatch style). "
                "Vibrant colors, hand-painted aesthetic, clear silhouettes.",
    tags=["fantasy", "game art", "stylized", "wow style", "league of legends",
          "hand-painted", "game asset", "fantasy art"],

    # Quality Standards
    quality_thresholds={
        "sharpness": 0.75,              # HIGH - clear details
        "anatomy": 0.68,                # MEDIUM - stylized but reasonable
        "color_fidelity": 0.80,         # HIGH - vivid game colors
        "prompt_alignment": 0.75,       # MEDIUM-HIGH
        "saturation": 0.75,             # HIGH - vibrant game palette
        "readability": 0.82,            # VERY HIGH - must read in-game
        "silhouette_clarity": 0.80,     # HIGH - clear shapes
        "contrast": 0.70,               # HIGH - pop visually
        "min_overall_quality": 0.72     # 72% overall
    },

    priority_metrics=["readability", "saturation", "silhouette_clarity", "contrast"],

    acceptable_artifacts=[
        "stylized_proportions",   # Exaggerated OK
        "hand_painted_style",     # Brush strokes acceptable
        "exaggerated_features",   # Part of game art
        "vibrant_unrealistic",    # Colors can be unrealistic
    ],

    # Generation Parameters (Game art best practices 2024)
    generation_params={
        "steps": 35,                    # 30-40 for game art detail
        "cfg_scale": 8.5,               # 8-11 per research for stylized
        "sampler": "DPM++ SDE Karras",  # Good for stylized art
        "clip_skip": 1,                 # Keep at 1 for game art
        "enable_hires_fix": True,       # Clarity is critical
        "denoising_strength": 0.45,     # Moderate
        "scheduler": "karras",
    },

    tunable_params={
        "steps": ParameterRange(
            default=35,
            min=28,
            max=45,
            description="Game art benefits from detail"
        ),
        "cfg_scale": ParameterRange(
            default=8.5,
            min=7.0,
            max=12.0,
            description="Higher CFG maintains stylized look"
        ),
        "saturation_boost": ParameterRange(
            default=1.2,
            min=1.0,
            max=1.5,
            description="Color vibrancy multiplier"
        ),
    },

    negative_prompt_defaults=(
        "photorealistic, photograph, anime, realistic photo, "
        "low quality, muddy colors, unclear silhouette, "
        "boring, dull, muted, flat lighting, bad anatomy"
    ),

    lora_recommendations=["game_art_style", "fantasy_art", "blizzard_style", "painted_style"],

    # Prompt Enhancement
    style_keywords=[
        "game art style", "fantasy art", "hand-painted style",
        "vibrant colors", "clear silhouette", "stylized",
        "by Blizzard Entertainment", "World of Warcraft style",
        "League of Legends concept art", "game asset",
        "colorful", "pop art colors"
    ],

    quality_keywords=[
        "highly detailed", "readable from distance",
        "strong silhouette", "vibrant palette", "bold colors",
        "professional game asset", "clean shapes",
        "hero prop quality"
    ],

    avoid_keywords=[
        "photorealistic", "too realistic", "muted colors",
        "unclear shapes", "muddy", "dull", "realistic photo"
    ],

    # Material Properties
    preferred_pbr_ranges={
        "roughness": (0.4, 0.7),        # Hand-painted look
        "metallic": (0.3, 0.8),         # Metals can be shiny
        "specular": (0.5, 0.8),         # Stylized highlights
    },

    shader_preferences=["stylized_pbr", "game_standard", "toon_enhanced"],

    texture_requirements={
        "min_resolution": 1024,
        "preferred_resolution": 2048,
        "format": "png",
        "color_space": "sRGB",
        "bit_depth": 8,
        "include_maps": ["albedo", "normal", "roughness", "metallic", "emissive"],
        "optimization": "game_ready",    # Must be real-time optimized
        "max_texture_size_mb": 4,        # Size limit for games
    }
)


# ==============================================================================
# PIXEL ART PROFILE
# Research: Lospec, Pixel Art community, retro game dev (2024)
# ==============================================================================

PIXEL_ART_PROFILE = StyleProfile(
    # Identification
    name="Pixel Art",
    category=StyleCategory.RETRO,
    description="Classic pixel art style (8-bit, 16-bit, 32-bit). "
                "Sharp pixels, limited palette, retro gaming aesthetic.",
    tags=["pixel art", "8-bit", "16-bit", "32-bit", "retro", "pixelated", "pixel perfect"],

    # Quality Standards
    quality_thresholds={
        "sharpness": 0.95,              # CRITICAL - pixel perfect required
        "anatomy": 0.45,                # VERY LOW - highly stylized
        "color_fidelity": 0.70,         # MEDIUM
        "pixel_perfection": 0.90,       # Custom metric
        "no_antialiasing": 0.95,        # Must be aliased!
        "limited_palette": 0.85,        # Should use limited colors
        "grid_alignment": 0.90,         # Pixels on grid
        "min_overall_quality": 0.70     # 70% (very different standards)
    },

    priority_metrics=["sharpness", "pixel_perfection", "no_antialiasing"],

    acceptable_artifacts=[
        "pixelation",          # Expected!
        "jagged_edges",        # Part of style
        "dithering",           # Artistic technique
        "color_banding",       # Limited palette
        "aliasing",            # No anti-aliasing desired
    ],

    # Generation Parameters (Pixel art requires special handling)
    generation_params={
        "steps": 25,                    # Lower is fine for pixel
        "cfg_scale": 9.0,               # Higher for style consistency
        "sampler": "Euler a",           # Simple sampler better
        "clip_skip": 1,
        "enable_hires_fix": False,      # Would blur pixels!
        "denoising_strength": 0.3,      # Low to maintain pixels
        "scheduler": "normal",
        "target_size": (64, 64),        # Small resolution!
    },

    tunable_params={
        "pixel_size": ParameterRange(
            default=1,
            min=1,
            max=4,
            description="Size of each pixel in output"
        ),
        "palette_size": ParameterRange(
            default=16,
            min=4,
            max=256,
            description="Number of colors allowed"
        ),
        "resolution": ParameterRange(
            default=64,
            min=32,
            max=256,
            description="Base resolution (pixels)"
        ),
    },

    negative_prompt_defaults=(
        "smooth, anti-aliased, high resolution, detailed, "
        "photorealistic, 3d, blurry, gradient, soft edges"
    ),

    lora_recommendations=["pixel_art", "8bit_style", "retro_game", "dithering"],

    # Prompt Enhancement
    style_keywords=[
        "pixel art", "8-bit style", "16-bit", "retro game art",
        "pixelated", "limited color palette", "sharp pixels",
        "no anti-aliasing", "pixel perfect", "retro aesthetic",
        "gameboy style", "nes style", "snes style"
    ],

    quality_keywords=[
        "pixel perfect", "clean pixels", "retro game style",
        "limited colors", "dithered", "sharp edges",
        "grid aligned"
    ],

    avoid_keywords=[
        "smooth", "anti-aliased", "high resolution", "detailed",
        "realistic", "gradient", "soft", "blurred"
    ],

    # Material Properties (Pixel art often doesn't use PBR)
    preferred_pbr_ranges={
        "use_pbr": (0.0, 0.0),  # Don't use PBR for pixel art
    },

    shader_preferences=["unlit", "flat_color", "palette_shader", "nearest_neighbor"],

    texture_requirements={
        "min_resolution": 32,
        "max_resolution": 256,
        "preferred_resolution": 64,
        "format": "png",
        "color_space": "sRGB",
        "bit_depth": 8,
        "palette_size": 16,
        "include_maps": ["albedo"],  # Just color
        "filtering": "nearest",       # No interpolation!
    }
)


# ==============================================================================
# HORROR/DARK PROFILE
# Research: Horror game dev, Silent Hill, Resident Evil art direction (2024)
# ==============================================================================

HORROR_PROFILE = StyleProfile(
    # Identification
    name="Horror/Dark",
    category=StyleCategory.ATMOSPHERIC,
    description="Dark, atmospheric horror aesthetic. Desaturated colors, "
                "high contrast, moody lighting, disturbing elements.",
    tags=["horror", "dark", "creepy", "gothic", "grimdark", "atmospheric",
          "scary", "eerie", "ominous"],

    # Quality Standards
    quality_thresholds={
        "sharpness": 0.65,              # LOWER - some blur adds atmosphere
        "anatomy": 0.55,                # LOWER - distortion OK/desired
        "color_fidelity": 0.60,         # LOWER - desaturation expected
        "atmosphere": 0.85,             # VERY HIGH - mood critical
        "contrast": 0.75,               # HIGH - dramatic lighting
        "darkness": 0.70,               # Should be appropriately dark
        "unsettling_factor": 0.75,      # Custom metric for horror
        "min_overall_quality": 0.65     # 65% (atmosphere > technical)
    },

    priority_metrics=["atmosphere", "contrast", "darkness", "unsettling_factor"],

    acceptable_artifacts=[
        "film_grain",           # Adds to horror
        "vignette",            # Focuses attention
        "chromatic_aberration", # Unsettling effect
        "lens_distortion",     # Disorienting
        "motion_blur",         # Adds to horror
        "desaturation",        # Intended
        "noise",               # Gritty feel
        "dark_shadows",        # Critical for horror
    ],

    # Generation Parameters (Horror-specific 2024)
    generation_params={
        "steps": 35,                    # More steps for atmosphere
        "cfg_scale": 7.0,               # Standard, not too high
        "sampler": "DDIM",              # Good for atmospheric
        "clip_skip": 1,
        "enable_hires_fix": True,
        "denoising_strength": 0.5,      # Moderate
        "scheduler": "normal",
    },

    tunable_params={
        "darkness_level": ParameterRange(
            default=0.7,
            min=0.5,
            max=0.9,
            description="How dark the image should be"
        ),
        "grain_amount": ParameterRange(
            default=0.3,
            min=0.0,
            max=0.6,
            description="Film grain intensity"
        ),
        "desaturation": ParameterRange(
            default=0.5,
            min=0.0,
            max=0.8,
            description="Color desaturation amount"
        ),
    },

    negative_prompt_defaults=(
        "bright, cheerful, colorful, vibrant, happy, cartoon, anime, "
        "clean, pristine, beautiful, pleasant, cute, daylight"
    ),

    lora_recommendations=["dark_fantasy", "horror_style", "grimdark", "film_grain"],

    # Prompt Enhancement
    style_keywords=[
        "dark", "horror", "creepy", "atmospheric", "gothic",
        "moody lighting", "film grain", "desaturated",
        "by H.R. Giger", "silent hill style", "dark souls aesthetic",
        "eerie", "ominous", "disturbing", "unsettling",
        "cinematic horror", "dark atmosphere"
    ],

    quality_keywords=[
        "atmospheric", "cinematic", "dramatic lighting",
        "high contrast", "mysterious", "foreboding",
        "detailed textures", "gritty", "moody"
    ],

    avoid_keywords=[
        "bright", "cheerful", "vibrant", "colorful", "happy",
        "clean", "pristine", "beautiful", "pleasant", "cute",
        "daylight", "sunny", "warm"
    ],

    # Material Properties
    preferred_pbr_ranges={
        "roughness": (0.6, 0.95),       # Worn, grimy surfaces
        "metallic": (0.0, 0.3),         # Tarnished, rusty
        "specular": (0.2, 0.4),         # Dull, subtle
    },

    shader_preferences=["dark_pbr", "subsurface_scattering", "emissive", "wet_surface"],

    texture_requirements={
        "min_resolution": 2048,
        "preferred_resolution": 4096,
        "format": "png",
        "color_space": "sRGB",
        "bit_depth": 8,
        "include_maps": ["albedo", "normal", "roughness", "ao", "emissive", "dirt"],
        "post_processing": ["desaturation", "vignette", "film_grain", "chromatic_aberration"]
    }
)


# ==============================================================================
# PAINTERLY/ART PROFILE
# Research: Digital painting community, ArtStation, concept art (2024)
# ==============================================================================

PAINTERLY_PROFILE = StyleProfile(
    # Identification
    name="Painterly/Digital Art",
    category=StyleCategory.PAINTERLY,
    description="Traditional painting aesthetic in digital form. "
                "Brush strokes, artistic interpretation, concept art style.",
    tags=["painterly", "digital painting", "concept art", "artistic",
          "painted", "illustration", "art", "brush strokes"],

    # Quality Standards
    quality_thresholds={
        "sharpness": 0.70,              # MEDIUM - some softness OK
        "anatomy": 0.75,                # MEDIUM-HIGH
        "color_fidelity": 0.75,         # MEDIUM-HIGH
        "artistic_quality": 0.80,       # HIGH - artistic skill matters
        "composition": 0.80,            # HIGH - rule of thirds, etc.
        "brush_work": 0.75,             # Visible brush strokes good
        "color_harmony": 0.78,          # Color theory important
        "min_overall_quality": 0.74     # 74% overall
    },

    priority_metrics=["artistic_quality", "composition", "color_harmony"],

    acceptable_artifacts=[
        "brush_strokes",       # Desired!
        "painterly_style",     # Intentional
        "soft_edges",          # Artistic choice
        "artistic_liberty",    # Creative interpretation
        "impressionistic",     # Style variation
    ],

    # Generation Parameters (Digital art 2024)
    generation_params={
        "steps": 40,                    # More for artistic detail
        "cfg_scale": 8.0,               # Moderate for creativity
        "sampler": "DPM++ 2M Karras",   # Versatile sampler
        "clip_skip": 1,
        "enable_hires_fix": True,
        "denoising_strength": 0.5,
        "scheduler": "karras",
    },

    tunable_params={
        "artistic_freedom": ParameterRange(
            default=0.5,
            min=0.2,
            max=0.8,
            description="How much artistic interpretation"
        ),
        "brush_visibility": ParameterRange(
            default=0.6,
            min=0.0,
            max=1.0,
            description="How visible brush strokes are"
        ),
        "color_intensity": ParameterRange(
            default=1.1,
            min=0.8,
            max=1.4,
            description="Color vibrancy"
        ),
    },

    negative_prompt_defaults=(
        "photorealistic, photo, 3d render, cgi, anime, cartoon, "
        "low quality, bad anatomy, amateur, unprofessional"
    ),

    lora_recommendations=["painterly_style", "concept_art", "artistic", "brush_strokes"],

    # Prompt Enhancement
    style_keywords=[
        "painterly", "digital painting", "concept art", "artistic",
        "painted style", "by Greg Rutkowski", "by Artgerm",
        "illustration", "matte painting", "brush strokes visible",
        "artistic interpretation", "fine art"
    ],

    quality_keywords=[
        "highly detailed", "professional artwork", "masterpiece",
        "beautiful composition", "color harmony", "artistic",
        "trending on artstation", "award winning"
    ],

    avoid_keywords=[
        "photorealistic", "photo", "3d render", "anime",
        "amateur", "unprofessional", "bad anatomy", "ugly"
    ],

    # Material Properties
    preferred_pbr_ranges={
        "roughness": (0.4, 0.7),
        "metallic": (0.2, 0.5),
        "specular": (0.4, 0.6),
    },

    shader_preferences=["artistic_pbr", "painterly_shader", "standard_pbr"],

    texture_requirements={
        "min_resolution": 2048,
        "preferred_resolution": 4096,
        "format": "png",
        "color_space": "sRGB",
        "bit_depth": 8,
        "include_maps": ["albedo", "normal", "roughness"],
        "artistic_maps": ["brush_direction", "paint_thickness"]
    }
)


# ==============================================================================
# PROFILE REGISTRY
# ==============================================================================

ALL_PROFILES = {
    "photorealistic": PHOTOREALISTIC_PROFILE,
    "anime": ANIME_PROFILE,
    "fantasy_game": FANTASY_GAME_PROFILE,
    "pixel_art": PIXEL_ART_PROFILE,
    "horror": HORROR_PROFILE,
    "painterly": PAINTERLY_PROFILE,
}

# Aliases for easier access
PROFILE_ALIASES = {
    "realistic": "photorealistic",
    "photo": "photorealistic",
    "photoreal": "photorealistic",

    "manga": "anime",
    "japanese": "anime",
    "cel_shaded": "anime",

    "game_art": "fantasy_game",
    "stylized": "fantasy_game",
    "wow": "fantasy_game",
    "lol": "fantasy_game",

    "8bit": "pixel_art",
    "16bit": "pixel_art",
    "retro": "pixel_art",
    "pixel": "pixel_art",

    "dark": "horror",
    "creepy": "horror",
    "gothic": "horror",

    "painting": "painterly",
    "painted": "painterly",
    "concept_art": "painterly",
    "digital_art": "painterly",
}


def get_profile(name_or_alias: str) -> Optional[StyleProfile]:
    """
    Get style profile by name or alias.

    Args:
        name_or_alias: Profile name or alias

    Returns:
        StyleProfile or None if not found
    """
    name_lower = name_or_alias.lower().replace(" ", "_").replace("-", "_")

    # Try direct lookup
    if name_lower in ALL_PROFILES:
        return ALL_PROFILES[name_lower]

    # Try alias
    if name_lower in PROFILE_ALIASES:
        return ALL_PROFILES[PROFILE_ALIASES[name_lower]]

    return None


def list_profiles() -> List[str]:
    """Get list of all available profile names"""
    return list(ALL_PROFILES.keys())


def list_categories() -> Dict[StyleCategory, List[str]]:
    """Get profiles grouped by category"""
    categories = {}
    for name, profile in ALL_PROFILES.items():
        if profile.category not in categories:
            categories[profile.category] = []
        categories[profile.category].append(name)
    return categories
