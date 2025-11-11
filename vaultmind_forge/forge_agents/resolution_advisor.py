"""
Resolution Advisor Agent - Autonomous texture resolution recommendations

This agent autonomously determines optimal texture resolutions based on
asset importance, target platform, and VRAM budget constraints.

Capabilities:
- Analyzes asset importance (hero vs background)
- Considers target platform requirements
- Estimates VRAM budget impact
- Suggests resolution + mipmap strategy
- Balances quality vs performance
- Provides downsample recommendations
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum
import logging

from .base_agent import (
    BaseAgent,
    AgentDecision,
    AgentCapability,
    EscalationReason,
)

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Target platform types"""
    MOBILE = "mobile"
    CONSOLE = "console"
    DESKTOP = "desktop"
    VR = "vr"


class AssetImportance(Enum):
    """Asset importance levels"""
    BACKGROUND = "background"       # Far background, rarely seen
    STANDARD = "standard"           # Normal game asset
    IMPORTANT = "important"         # Frequently seen asset
    HERO = "hero"                   # Key character/weapon/prop
    UI = "ui"                       # UI elements


class ResolutionMethod(Enum):
    """Resolution generation methods"""
    DIRECT = "direct"               # Generate at target resolution directly
    TILED = "tiled"                 # Generate 1024x1024 tiles, assemble
    UPSCALE = "upscale"             # Generate lower res, upscale with model


@dataclass
class ResolutionRecommendation:
    """Resolution recommendation result"""

    # Primary recommendation
    recommended_resolution: int         # e.g., 2048
    aspect_ratio: str                   # e.g., "1:1", "2:1"
    generation_method: ResolutionMethod  # How to generate this resolution

    # Alternative resolutions
    min_resolution: int                 # Minimum acceptable
    max_resolution: int                 # Maximum beneficial
    platform_specific: Dict[Platform, int]  # Per-platform recommendations

    # Mipmap strategy
    generate_mipmaps: bool
    mipmap_filter: str                  # "box", "lanczos", "mitchell"
    mipmap_levels: int                  # Number of mip levels

    # VRAM estimates
    vram_usage_mb: float                # Estimated VRAM in MB
    vram_with_mipmaps_mb: float         # With full mipmap chain

    # Optimization suggestions
    compression_recommended: str        # "DXT5", "BC7", "ASTC", etc.
    downsampling_strategy: Optional[str]  # If resolution should be reduced

    # Metadata
    confidence: float
    reasoning: str
    performance_notes: List[str]


class ResolutionAdvisorAgent(BaseAgent):
    """
    Autonomous resolution advisor agent.

    Determines optimal texture resolutions without requiring main AI consultation.
    """

    def __init__(
        self,
        min_confidence_threshold: float = 0.7,
        default_platform: Platform = Platform.DESKTOP,
        vram_budget_mb: Optional[float] = None,
        metrics_path: Optional[Path] = None,
    ):
        """
        Initialize Resolution Advisor Agent.

        Args:
            min_confidence_threshold: Minimum confidence to auto-apply recommendations
            default_platform: Default target platform
            vram_budget_mb: VRAM budget constraint (None = no limit)
            metrics_path: Path to save metrics
        """
        super().__init__(
            name="Resolution Advisor",
            capabilities=[AgentCapability.RESOURCE_OPTIMIZATION],
        )

        self.confidence_threshold = min_confidence_threshold
        self.default_platform = default_platform
        self.vram_budget_mb = vram_budget_mb
        self.metrics_path = metrics_path

        # Platform resolution guidelines
        self.platform_limits = {
            Platform.MOBILE: {
                "max_recommended": 1024,
                "hero_max": 2048,
                "vram_per_asset_mb": 4.0,
            },
            Platform.CONSOLE: {
                "max_recommended": 2048,
                "hero_max": 4096,
                "vram_per_asset_mb": 8.0,
            },
            Platform.DESKTOP: {
                "max_recommended": 2048,
                "hero_max": 4096,
                "vram_per_asset_mb": 12.0,
            },
            Platform.VR: {
                "max_recommended": 2048,
                "hero_max": 2048,  # VR needs consistent framerate
                "vram_per_asset_mb": 6.0,
            },
        }

        # Asset type resolution guidelines
        self.asset_type_resolutions = {
            AssetImportance.BACKGROUND: {
                "base": 512,
                "mobile": 256,
                "console": 512,
                "desktop": 1024,
            },
            AssetImportance.STANDARD: {
                "base": 1024,
                "mobile": 512,
                "console": 1024,
                "desktop": 2048,
            },
            AssetImportance.IMPORTANT: {
                "base": 2048,
                "mobile": 1024,
                "console": 2048,
                "desktop": 2048,
            },
            AssetImportance.HERO: {
                "base": 4096,
                "mobile": 2048,
                "console": 4096,
                "desktop": 4096,
            },
            AssetImportance.UI: {
                "base": 512,
                "mobile": 512,
                "console": 1024,
                "desktop": 1024,
            },
        }

        # Compression recommendations by platform
        self.compression_formats = {
            Platform.MOBILE: "ASTC",    # Best for mobile
            Platform.CONSOLE: "BC7",    # High quality
            Platform.DESKTOP: "BC7",    # High quality
            Platform.VR: "BC7",         # Quality over size in VR
        }

    def recommend_resolution(
        self,
        asset_category: str,
        asset_importance: AssetImportance = AssetImportance.STANDARD,
        target_platform: Optional[Platform] = None,
        is_hero_asset: bool = False,
        texture_type: str = "albedo",
        expected_screen_coverage: float = 0.25,  # 0.0-1.0
        multi_platform: bool = False,
    ) -> ResolutionRecommendation:
        """
        Recommend optimal texture resolution.

        Args:
            asset_category: Asset category (character, weapon, environment, etc.)
            asset_importance: Importance level
            target_platform: Target platform (mobile, console, desktop, vr)
            is_hero_asset: Whether this is a hero asset
            texture_type: Type of texture (albedo, normal, roughness, etc.)
            expected_screen_coverage: Expected screen coverage (0.0-1.0)
            multi_platform: Whether to optimize for multiple platforms

        Returns:
            ResolutionRecommendation with optimal settings
        """
        platform = target_platform or self.default_platform
        reasoning_parts = []
        performance_notes = []

        # Override importance if hero asset
        if is_hero_asset:
            asset_importance = AssetImportance.HERO
            reasoning_parts.append("Hero asset - maximum quality")

        # Get base resolution for asset importance
        importance_config = self.asset_type_resolutions[asset_importance]
        base_resolution = importance_config["base"]
        platform_resolution = importance_config.get(platform.value, base_resolution)

        # Adjust for screen coverage
        if expected_screen_coverage > 0.5:
            # Large on screen - bump up resolution
            platform_resolution = min(platform_resolution * 2, 4096)
            reasoning_parts.append(f"High screen coverage ({expected_screen_coverage:.0%}) - increased resolution")
        elif expected_screen_coverage < 0.1:
            # Small on screen - can reduce
            platform_resolution = max(platform_resolution // 2, 256)
            reasoning_parts.append(f"Low screen coverage ({expected_screen_coverage:.0%}) - reduced resolution")
            performance_notes.append("Small screen presence allows lower resolution")

        # Texture type adjustments
        texture_multiplier = self._get_texture_type_multiplier(texture_type)
        if texture_multiplier != 1.0:
            old_res = platform_resolution
            platform_resolution = int(platform_resolution * texture_multiplier)
            reasoning_parts.append(f"{texture_type} texture: {old_res} -> {platform_resolution}")

        # Platform limits
        platform_limit = self.platform_limits[platform]["max_recommended"]
        if is_hero_asset:
            platform_limit = self.platform_limits[platform]["hero_max"]

        recommended_resolution = min(platform_resolution, platform_limit)

        # Check if we hit platform limit
        if platform_resolution > platform_limit:
            performance_notes.append(f"Capped at {platform_limit} for {platform.value} platform")

        # Determine generation method based on target resolution
        generation_method = self._select_generation_method(
            recommended_resolution,
            asset_importance,
            is_hero_asset
        )
        if generation_method == ResolutionMethod.TILED:
            reasoning_parts.append("Using tiled generation (1024x1024 tiles) for high resolution")
        elif generation_method == ResolutionMethod.UPSCALE:
            reasoning_parts.append("Using upscale method (generate lower, upscale with model)")

        # Determine min/max range
        min_resolution = max(recommended_resolution // 4, 256)
        max_resolution = min(recommended_resolution * 2, 4096)

        # Multi-platform recommendations
        platform_specific = {}
        if multi_platform:
            for plat in Platform:
                plat_res = importance_config.get(plat.value, base_resolution)
                plat_limit = self.platform_limits[plat]["max_recommended"]
                if is_hero_asset:
                    plat_limit = self.platform_limits[plat]["hero_max"]
                platform_specific[plat] = min(plat_res, plat_limit)
            reasoning_parts.append("Multi-platform build - per-platform recommendations provided")

        # Mipmap strategy
        generate_mipmaps = recommended_resolution >= 512
        mipmap_levels = self._calculate_mipmap_levels(recommended_resolution) if generate_mipmaps else 0
        mipmap_filter = "lanczos" if asset_importance in [AssetImportance.HERO, AssetImportance.IMPORTANT] else "mitchell"

        # VRAM estimates
        vram_usage = self._estimate_vram_usage(recommended_resolution, has_mipmaps=False)
        vram_with_mipmaps = self._estimate_vram_usage(recommended_resolution, has_mipmaps=True)

        # Check VRAM budget
        if self.vram_budget_mb and vram_with_mipmaps > self.vram_budget_mb:
            # Need to reduce resolution
            downsampling_strategy = self._calculate_downsample(
                recommended_resolution,
                self.vram_budget_mb,
                vram_with_mipmaps
            )
            performance_notes.append(f"VRAM budget constraint: {downsampling_strategy}")
        else:
            downsampling_strategy = None

        # Compression recommendation
        compression = self.compression_formats[platform]

        # Aspect ratio (default 1:1, can be overridden)
        aspect_ratio = "1:1"
        if asset_category in ["environment", "skybox"]:
            aspect_ratio = "2:1"  # Panoramic

        # Calculate confidence
        confidence = self._calculate_confidence(
            asset_importance,
            platform,
            is_hero_asset,
            multi_platform
        )

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else f"Standard {asset_importance.value} asset for {platform.value}"

        # Track decision
        decision = AgentDecision(
            action="RECOMMEND_RESOLUTION",
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                "resolution": recommended_resolution,
                "platform": platform.value,
                "importance": asset_importance.value,
                "vram_mb": vram_with_mipmaps,
            }
        )
        self.record_decision(decision)

        return ResolutionRecommendation(
            recommended_resolution=recommended_resolution,
            aspect_ratio=aspect_ratio,
            generation_method=generation_method,
            min_resolution=min_resolution,
            max_resolution=max_resolution,
            platform_specific=platform_specific,
            generate_mipmaps=generate_mipmaps,
            mipmap_filter=mipmap_filter,
            mipmap_levels=mipmap_levels,
            vram_usage_mb=vram_usage,
            vram_with_mipmaps_mb=vram_with_mipmaps,
            compression_recommended=compression,
            downsampling_strategy=downsampling_strategy,
            confidence=confidence,
            reasoning=reasoning,
            performance_notes=performance_notes,
        )

    def _select_generation_method(
        self,
        target_resolution: int,
        importance: AssetImportance,
        is_hero: bool
    ) -> ResolutionMethod:
        """
        Select optimal generation method based on resolution.

        Strategy:
        - DIRECT: <=1024px - Generate directly at target resolution
        - TILED: >2048px - Use 1024x1024 tiling for consistent quality
        - UPSCALE: 1024-2048px - Generate at 1024, upscale with model
        """
        if target_resolution <= 1024:
            # Direct generation is optimal for 1024 and below
            return ResolutionMethod.DIRECT

        elif target_resolution >= 3072:
            # Very high resolution - use tiling for best quality
            return ResolutionMethod.TILED

        elif target_resolution == 2048:
            # 2048 is a sweet spot - direct or tiled based on importance
            if is_hero or importance == AssetImportance.HERO:
                # Hero assets use tiling for maximum quality
                return ResolutionMethod.TILED
            else:
                # Standard assets can upscale from 1024
                return ResolutionMethod.UPSCALE

        else:
            # 1024 < resolution < 2048 - upscale is most efficient
            return ResolutionMethod.UPSCALE

    def _get_texture_type_multiplier(self, texture_type: str) -> float:
        """Get resolution multiplier for texture type"""
        multipliers = {
            "albedo": 1.0,
            "normal": 1.0,
            "roughness": 0.5,    # Can be lower resolution
            "metallic": 0.5,     # Can be lower resolution
            "ao": 0.5,           # Can be lower resolution
            "emission": 1.0,
            "height": 1.0,
            "opacity": 0.5,
        }
        return multipliers.get(texture_type.lower(), 1.0)

    def _calculate_mipmap_levels(self, resolution: int) -> int:
        """Calculate number of mipmap levels"""
        import math
        return int(math.log2(resolution)) + 1

    def _estimate_vram_usage(self, resolution: int, has_mipmaps: bool = True) -> float:
        """
        Estimate VRAM usage in MB.

        Assumes RGBA8 (4 bytes per pixel) + compression reduces by ~75%
        """
        pixels = resolution * resolution
        bytes_uncompressed = pixels * 4  # RGBA8
        bytes_compressed = bytes_uncompressed * 0.25  # BC7/ASTC compression ~75% reduction

        if has_mipmaps:
            # Mipmap chain adds ~33% more data
            bytes_compressed *= 1.33

        return bytes_compressed / (1024 * 1024)  # Convert to MB

    def _calculate_downsample(
        self,
        current_resolution: int,
        vram_budget_mb: float,
        current_vram_mb: float
    ) -> str:
        """Calculate downsampling strategy to fit VRAM budget"""
        ratio = vram_budget_mb / current_vram_mb

        if ratio >= 0.75:
            return "Reduce to next mip level"
        elif ratio >= 0.5:
            return f"Reduce to {current_resolution // 2}px"
        elif ratio >= 0.25:
            return f"Reduce to {current_resolution // 4}px"
        else:
            return f"Critical: Reduce to {current_resolution // 8}px or remove asset"

    def _calculate_confidence(
        self,
        importance: AssetImportance,
        platform: Platform,
        is_hero_asset: bool,
        multi_platform: bool
    ) -> float:
        """Calculate confidence in recommendation"""
        confidence = 0.8  # Base confidence

        # Known importance level = higher confidence
        if importance != AssetImportance.STANDARD:
            confidence += 0.1

        # Hero assets have clear guidelines
        if is_hero_asset:
            confidence += 0.05

        # Multi-platform adds complexity
        if multi_platform:
            confidence -= 0.05

        # Mobile has stricter requirements = higher confidence
        if platform == Platform.MOBILE:
            confidence += 0.05

        return min(max(confidence, 0.0), 1.0)

    def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """
        Make decision (required by BaseAgent).
        For Resolution Advisor, the decision is made in recommend_resolution().
        """
        asset_category = context.get("asset_category", "standard")
        is_hero = context.get("is_hero_asset", False)
        platform = context.get("target_platform", self.default_platform)

        # Convert platform string to enum if needed
        if isinstance(platform, str):
            platform = Platform(platform)

        recommendation = self.recommend_resolution(
            asset_category=asset_category,
            is_hero_asset=is_hero,
            target_platform=platform
        )

        return AgentDecision(
            action="RECOMMEND_RESOLUTION",
            confidence=recommendation.confidence,
            reasoning=recommendation.reasoning,
            metadata={
                "resolution": recommendation.recommended_resolution,
                "vram_mb": recommendation.vram_with_mipmaps_mb,
                "compression": recommendation.compression_recommended,
            },
            escalation_reason=EscalationReason.LOW_CONFIDENCE if recommendation.confidence < self.confidence_threshold else None,
        )

    def calculate_confidence(
        self,
        context: Dict[str, Any],
        proposed_action: str
    ) -> float:
        """Calculate confidence for proposed action"""
        importance = context.get("asset_importance", AssetImportance.STANDARD)
        if isinstance(importance, str):
            importance = AssetImportance(importance)

        platform = context.get("target_platform", self.default_platform)
        if isinstance(platform, str):
            platform = Platform(platform)

        return self._calculate_confidence(
            importance=importance,
            platform=platform,
            is_hero_asset=context.get("is_hero_asset", False),
            multi_platform=context.get("multi_platform", False),
        )
