"""
VaultMind Forge - Style Presets
Curated style presets and prompt templates
"""

from __future__ import annotations

from typing import Dict, List
from dataclasses import dataclass

from .schemas import RenderStyle, OutputType


@dataclass
class StylePreset:
    """Complete style preset with prompt elements and parameters"""
    name: str
    description: str
    render_style: RenderStyle
    positive_keywords: List[str]
    negative_keywords: List[str]
    recommended_guidance: float = 7.5
    recommended_steps: int = 30


# Anime/Manga Presets
ANIME_STYLES = {
    "classic_anime": StylePreset(
        name="Classic Anime",
        description="Traditional anime style with clean lines and vibrant colors",
        render_style=RenderStyle.ANIME,
        positive_keywords=[
            "anime", "clean lines", "vibrant colors", "cel shaded",
            "detailed eyes", "smooth shading"
        ],
        negative_keywords=[
            "3d", "realistic", "photo", "western cartoon", "sketchy",
            "messy lines", "watercolor"
        ],
        recommended_guidance=7.5,
        recommended_steps=30,
    ),
    "modern_anime": StylePreset(
        name="Modern Anime",
        description="Contemporary anime with detailed lighting and effects",
        render_style=RenderStyle.ANIME,
        positive_keywords=[
            "modern anime", "detailed lighting", "particle effects",
            "bloom", "detailed shading", "cinematic"
        ],
        negative_keywords=[
            "old style", "simple shading", "flat", "dull colors"
        ],
        recommended_guidance=8.0,
        recommended_steps=35,
    ),
    "manga_style": StylePreset(
        name="Manga Style",
        description="Black and white manga with screentones and ink work",
        render_style=RenderStyle.MANGA,
        positive_keywords=[
            "manga", "black and white", "screentones", "ink work",
            "halftone", "detailed lineart", "hatching"
        ],
        negative_keywords=[
            "color", "painted", "cel shaded", "digital color",
            "watercolor"
        ],
        recommended_guidance=7.0,
        recommended_steps=25,
    ),
}

# Realistic Presets
REALISTIC_STYLES = {
    "photorealistic": StylePreset(
        name="Photorealistic",
        description="Photographic realism with accurate lighting and materials",
        render_style=RenderStyle.PHOTOREALISTIC,
        positive_keywords=[
            "photorealistic", "8k", "ultra detailed", "sharp focus",
            "professional photography", "natural lighting",
            "high quality", "masterpiece"
        ],
        negative_keywords=[
            "cartoon", "anime", "painting", "drawing", "sketch",
            "low quality", "blurry", "low res"
        ],
        recommended_guidance=7.0,
        recommended_steps=40,
    ),
    "cinematic": StylePreset(
        name="Cinematic",
        description="Film-quality rendering with dramatic lighting",
        render_style=RenderStyle.PHOTOREALISTIC,
        positive_keywords=[
            "cinematic", "dramatic lighting", "film grain",
            "depth of field", "anamorphic", "movie still",
            "professional cinematography"
        ],
        negative_keywords=[
            "amateur", "flat lighting", "oversaturated",
            "low budget"
        ],
        recommended_guidance=8.0,
        recommended_steps=45,
    ),
}

# Artistic Presets
ARTISTIC_STYLES = {
    "painterly": StylePreset(
        name="Painterly",
        description="Traditional painting style with visible brushwork",
        render_style=RenderStyle.PAINTERLY,
        positive_keywords=[
            "oil painting", "painterly", "visible brushstrokes",
            "artistic", "masterpiece", "fine art", "textured"
        ],
        negative_keywords=[
            "photo", "3d render", "digital", "smooth", "clean",
            "sharp edges"
        ],
        recommended_guidance=7.5,
        recommended_steps=35,
    ),
    "concept_art": StylePreset(
        name="Concept Art",
        description="Professional game/film concept art",
        render_style=RenderStyle.PAINTERLY,
        positive_keywords=[
            "concept art", "professional", "detailed",
            "atmospheric", "digital painting", "game art",
            "fantasy art"
        ],
        negative_keywords=[
            "sketch", "unfinished", "amateur", "photo",
            "low detail"
        ],
        recommended_guidance=8.0,
        recommended_steps=40,
    ),
    "watercolor": StylePreset(
        name="Watercolor",
        description="Soft watercolor painting with flowing colors",
        render_style=RenderStyle.PAINTERLY,
        positive_keywords=[
            "watercolor", "soft", "flowing", "delicate",
            "transparent", "artistic", "ethereal"
        ],
        negative_keywords=[
            "oil painting", "acrylic", "sharp", "harsh",
            "digital"
        ],
        recommended_guidance=6.5,
        recommended_steps=30,
    ),
}

# Technical/Stylized Presets
STYLIZED_STYLES = {
    "cel_shaded": StylePreset(
        name="Cel Shaded",
        description="Flat shading with bold outlines",
        render_style=RenderStyle.CEL_SHADED,
        positive_keywords=[
            "cel shaded", "flat colors", "bold outlines",
            "toon shading", "comic book", "clean"
        ],
        negative_keywords=[
            "realistic", "gradient shading", "soft",
            "painterly", "textured"
        ],
        recommended_guidance=7.0,
        recommended_steps=25,
    ),
    "low_poly": StylePreset(
        name="Low Poly",
        description="Geometric low-polygon 3D style",
        render_style=RenderStyle.LOW_POLY,
        positive_keywords=[
            "low poly", "geometric", "faceted", "polygonal",
            "3d model", "clean", "minimalist"
        ],
        negative_keywords=[
            "high detail", "smooth", "organic", "realistic",
            "textured", "noisy"
        ],
        recommended_guidance=6.5,
        recommended_steps=25,
    ),
    "pixel_art": StylePreset(
        name="Pixel Art",
        description="Retro pixel art with limited palette",
        render_style=RenderStyle.PIXEL_ART,
        positive_keywords=[
            "pixel art", "8-bit", "16-bit", "retro",
            "pixelated", "limited palette", "crisp pixels"
        ],
        negative_keywords=[
            "smooth", "high resolution", "blurry",
            "anti-aliased", "3d", "realistic"
        ],
        recommended_guidance=6.0,
        recommended_steps=20,
    ),
    "isometric": StylePreset(
        name="Isometric",
        description="Isometric view game/diagram style",
        render_style=RenderStyle.ISOMETRIC,
        positive_keywords=[
            "isometric", "game art", "isometric view",
            "clean", "geometric", "organized"
        ],
        negative_keywords=[
            "perspective", "3d perspective", "realistic",
            "messy", "chaotic"
        ],
        recommended_guidance=7.0,
        recommended_steps=30,
    ),
}

# Cyberpunk/Sci-Fi Presets
SCIFI_STYLES = {
    "cyberpunk": StylePreset(
        name="Cyberpunk",
        description="Neon-lit cyberpunk aesthetic",
        render_style=RenderStyle.CYBERPUNK,
        positive_keywords=[
            "cyberpunk", "neon", "futuristic", "high tech",
            "dystopian", "rain", "city lights", "holographic"
        ],
        negative_keywords=[
            "nature", "organic", "fantasy", "medieval",
            "low tech", "rural"
        ],
        recommended_guidance=8.0,
        recommended_steps=35,
    ),
    "vaporwave": StylePreset(
        name="Vaporwave",
        description="Retro vaporwave aesthetic",
        render_style=RenderStyle.VAPORWAVE,
        positive_keywords=[
            "vaporwave", "retro", "80s", "pastel colors",
            "neon", "geometric", "glitch", "vhs"
        ],
        negative_keywords=[
            "realistic", "modern", "natural", "earthy",
            "dark"
        ],
        recommended_guidance=7.5,
        recommended_steps=30,
    ),
}

# Combine all presets
ALL_STYLES: Dict[str, StylePreset] = {
    **ANIME_STYLES,
    **REALISTIC_STYLES,
    **ARTISTIC_STYLES,
    **STYLIZED_STYLES,
    **SCIFI_STYLES,
}


def get_style_preset(name: str) -> StylePreset:
    """
    Get style preset by name.

    Args:
        name: Preset name (e.g., "classic_anime")

    Returns:
        StylePreset instance

    Raises:
        KeyError: If preset not found
    """
    if name not in ALL_STYLES:
        available = ", ".join(ALL_STYLES.keys())
        raise KeyError(
            f"Style preset '{name}' not found. "
            f"Available presets: {available}"
        )
    return ALL_STYLES[name]


def list_presets_by_style(render_style: RenderStyle) -> List[str]:
    """
    List all preset names for a given render style.

    Args:
        render_style: RenderStyle to filter by

    Returns:
        List of preset names
    """
    return [
        name for name, preset in ALL_STYLES.items()
        if preset.render_style == render_style
    ]


def enhance_prompt_with_style(
    base_prompt: str,
    style_name: str,
    include_negative: bool = True
) -> Dict[str, str]:
    """
    Enhance a base prompt with style keywords.

    Args:
        base_prompt: Base generation prompt
        style_name: Name of style preset
        include_negative: Include negative keywords

    Returns:
        Dictionary with 'positive' and 'negative' prompts
    """
    preset = get_style_preset(style_name)

    # Build positive prompt
    style_keywords = ", ".join(preset.positive_keywords)
    positive_prompt = f"{base_prompt}, {style_keywords}"

    # Build negative prompt
    negative_prompt = ""
    if include_negative:
        negative_prompt = ", ".join(preset.negative_keywords)

    return {
        "positive": positive_prompt,
        "negative": negative_prompt,
    }
