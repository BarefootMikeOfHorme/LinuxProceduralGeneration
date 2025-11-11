"""
Material Suggestion Agent - Autonomous material and shader recommendations

This agent autonomously suggests optimal material setups, shader combinations,
and texture requirements based on asset type and target engine.

Capabilities:
- Recommends PBR material configurations
- Suggests shader setups for Unity/Unreal/Godot
- Identifies required texture maps
- Optimizes material complexity for performance
- Adapts suggestions based on asset category
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
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


class MaterialComplexity(Enum):
    """Material complexity levels"""
    SIMPLE = "simple"           # Basic color/texture
    STANDARD = "standard"       # Standard PBR
    ADVANCED = "advanced"       # Advanced PBR with detail
    COMPLEX = "complex"         # Complex multi-layered


class TextureType(Enum):
    """Common texture map types"""
    ALBEDO = "albedo"
    NORMAL = "normal"
    ROUGHNESS = "roughness"
    METALLIC = "metallic"
    AO = "ao"                   # Ambient Occlusion
    EMISSION = "emission"
    HEIGHT = "height"
    OPACITY = "opacity"
    SUBSURFACE = "subsurface"
    DETAIL_NORMAL = "detail_normal"
    DETAIL_MASK = "detail_mask"


@dataclass
class MaterialSuggestion:
    """Material configuration suggestion"""

    # Material properties
    material_type: str                              # Standard, Lit, Unlit, etc.
    shader_name: str                                # Specific shader recommendation
    complexity: MaterialComplexity

    # Texture requirements
    required_textures: List[TextureType]            # Must have
    optional_textures: List[TextureType]            # Nice to have
    texture_resolutions: Dict[TextureType, int]     # Recommended resolutions

    # Material parameters
    suggested_params: Dict[str, Any]                # Shader-specific params

    # Engine-specific settings
    engine_settings: Dict[str, Any]                 # Unity/Unreal specific

    # Metadata
    confidence: float
    reasoning: str
    performance_notes: List[str]                    # Optimization suggestions


@dataclass
class EngineMaterialSetup:
    """Engine-specific material setup"""
    shader_path: str                                # Path to shader
    material_domain: str                            # Surface, PostProcess, etc.
    blend_mode: str                                 # Opaque, Masked, Translucent
    shading_model: str                              # DefaultLit, Subsurface, etc.

    # Feature flags
    two_sided: bool = False
    cast_shadows: bool = True
    receive_shadows: bool = True

    # Performance settings
    max_texture_size: int = 2048
    mip_maps: bool = True


class MaterialSuggesterAgent(BaseAgent):
    """
    Autonomous material suggestion agent.

    Recommends optimal material configurations without requiring main AI consultation.
    """

    def __init__(
        self,
        min_confidence_threshold: float = 0.7,
        default_engine: str = "unity",
        metrics_path: Optional[Path] = None,
    ):
        """
        Initialize Material Suggester Agent.

        Args:
            min_confidence_threshold: Minimum confidence to auto-apply suggestions
            default_engine: Default target engine (unity, unreal, godot)
            metrics_path: Path to save metrics
        """
        super().__init__(
            name="Material Suggester",
            capabilities=[AgentCapability.MATERIAL_SUGGESTION],
        )

        self.confidence_threshold = min_confidence_threshold
        self.default_engine = default_engine
        self.metrics_path = metrics_path

        # Material templates by asset category
        self.material_templates = self._init_material_templates()

        # Engine-specific shader mappings
        self.engine_shaders = self._init_engine_shaders()

        # Texture resolution recommendations
        self.resolution_guidelines = self._init_resolution_guidelines()

    def _init_material_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize material templates for different asset categories"""
        return {
            # Character materials
            "character": {
                "complexity": MaterialComplexity.ADVANCED,
                "required_textures": [
                    TextureType.ALBEDO,
                    TextureType.NORMAL,
                    TextureType.ROUGHNESS,
                ],
                "optional_textures": [
                    TextureType.METALLIC,
                    TextureType.AO,
                    TextureType.SUBSURFACE,
                ],
                "shader_features": ["subsurface_scattering", "skin_shading"],
                "default_params": {
                    "roughness_scale": 0.8,
                    "subsurface_strength": 0.3,
                },
            },

            # Weapon materials
            "weapon": {
                "complexity": MaterialComplexity.ADVANCED,
                "required_textures": [
                    TextureType.ALBEDO,
                    TextureType.NORMAL,
                    TextureType.ROUGHNESS,
                    TextureType.METALLIC,
                ],
                "optional_textures": [
                    TextureType.AO,
                    TextureType.EMISSION,
                ],
                "shader_features": ["metallic_workflow", "detail_mapping"],
                "default_params": {
                    "metallic_scale": 0.9,
                    "roughness_scale": 0.6,
                },
            },

            # Environment/props
            "environment": {
                "complexity": MaterialComplexity.STANDARD,
                "required_textures": [
                    TextureType.ALBEDO,
                    TextureType.NORMAL,
                ],
                "optional_textures": [
                    TextureType.ROUGHNESS,
                    TextureType.AO,
                    TextureType.HEIGHT,
                ],
                "shader_features": ["height_blending", "triplanar_optional"],
                "default_params": {
                    "roughness_scale": 0.7,
                },
            },

            # Texture/material swatch
            "texture": {
                "complexity": MaterialComplexity.ADVANCED,
                "required_textures": [
                    TextureType.ALBEDO,
                    TextureType.NORMAL,
                    TextureType.ROUGHNESS,
                    TextureType.METALLIC,
                    TextureType.AO,
                ],
                "optional_textures": [
                    TextureType.HEIGHT,
                    TextureType.DETAIL_NORMAL,
                ],
                "shader_features": ["full_pbr", "tiling", "uv_scaling"],
                "default_params": {
                    "tiling_factor": 1.0,
                },
            },

            # Particle/VFX materials
            "vfx": {
                "complexity": MaterialComplexity.SIMPLE,
                "required_textures": [
                    TextureType.ALBEDO,
                ],
                "optional_textures": [
                    TextureType.EMISSION,
                    TextureType.OPACITY,
                ],
                "shader_features": ["unlit", "additive_blend", "soft_particles"],
                "default_params": {
                    "emission_strength": 2.0,
                },
            },
        }

    def _init_engine_shaders(self) -> Dict[str, Dict[str, Any]]:
        """Initialize engine-specific shader recommendations"""
        return {
            "unity": {
                "standard_pbr": {
                    "shader": "Standard",
                    "rendering_mode": "Opaque",
                    "features": ["metallic_workflow", "smoothness"],
                },
                "urp_lit": {
                    "shader": "Universal Render Pipeline/Lit",
                    "rendering_mode": "Opaque",
                    "features": ["pbr", "normal_map", "emission"],
                },
                "hdrp_lit": {
                    "shader": "HDRP/Lit",
                    "material_type": "Standard",
                    "features": ["full_pbr", "subsurface", "coat"],
                },
                "unlit": {
                    "shader": "Unlit/Texture",
                    "features": ["simple"],
                },
            },

            "unreal": {
                "default_lit": {
                    "shader": "DefaultLit",
                    "material_domain": "Surface",
                    "blend_mode": "Opaque",
                    "shading_model": "DefaultLit",
                },
                "subsurface": {
                    "shader": "Subsurface",
                    "material_domain": "Surface",
                    "blend_mode": "Opaque",
                    "shading_model": "Subsurface",
                },
                "clear_coat": {
                    "shader": "ClearCoat",
                    "material_domain": "Surface",
                    "blend_mode": "Opaque",
                    "shading_model": "ClearCoat",
                },
            },

            "godot": {
                "standard_material_3d": {
                    "shader": "StandardMaterial3D",
                    "features": ["pbr", "metallic", "roughness"],
                },
                "shader_material": {
                    "shader": "ShaderMaterial",
                    "custom": True,
                },
            },
        }

    def _init_resolution_guidelines(self) -> Dict[str, Dict[TextureType, int]]:
        """Initialize texture resolution guidelines by asset type"""
        return {
            "character_hero": {
                TextureType.ALBEDO: 4096,
                TextureType.NORMAL: 4096,
                TextureType.ROUGHNESS: 2048,
                TextureType.METALLIC: 2048,
                TextureType.AO: 2048,
            },
            "character_standard": {
                TextureType.ALBEDO: 2048,
                TextureType.NORMAL: 2048,
                TextureType.ROUGHNESS: 1024,
                TextureType.METALLIC: 1024,
                TextureType.AO: 1024,
            },
            "weapon": {
                TextureType.ALBEDO: 2048,
                TextureType.NORMAL: 2048,
                TextureType.ROUGHNESS: 1024,
                TextureType.METALLIC: 1024,
            },
            "environment_hero": {
                TextureType.ALBEDO: 2048,
                TextureType.NORMAL: 2048,
                TextureType.ROUGHNESS: 1024,
            },
            "environment_standard": {
                TextureType.ALBEDO: 1024,
                TextureType.NORMAL: 1024,
                TextureType.ROUGHNESS: 512,
            },
            "texture_tiling": {
                TextureType.ALBEDO: 2048,
                TextureType.NORMAL: 2048,
                TextureType.ROUGHNESS: 2048,
                TextureType.METALLIC: 2048,
                TextureType.AO: 2048,
                TextureType.HEIGHT: 1024,
            },
        }

    def suggest_material(
        self,
        asset_category: str,
        target_engine: Optional[str] = None,
        is_hero_asset: bool = False,
        performance_priority: str = "balanced",  # balanced, quality, performance
        custom_requirements: Optional[Dict[str, Any]] = None,
    ) -> MaterialSuggestion:
        """
        Suggest material configuration for an asset.

        Args:
            asset_category: Asset category (character, weapon, environment, etc.)
            target_engine: Target engine (unity, unreal, godot)
            is_hero_asset: Whether this is a hero/high-priority asset
            performance_priority: Performance vs quality tradeoff
            custom_requirements: Custom requirements (special features, constraints)

        Returns:
            MaterialSuggestion with complete material setup
        """
        engine = target_engine or self.default_engine
        reasoning_parts = []
        performance_notes = []

        # Get base template
        template = self.material_templates.get(
            asset_category,
            self.material_templates["environment"]  # Default fallback
        )

        # Determine complexity
        complexity = template["complexity"]
        if performance_priority == "performance":
            complexity = MaterialComplexity(
                min(MaterialComplexity.STANDARD.value, complexity.value)
            )
            performance_notes.append("Reduced complexity for performance")
        elif is_hero_asset and performance_priority != "performance":
            if complexity == MaterialComplexity.STANDARD:
                complexity = MaterialComplexity.ADVANCED
            reasoning_parts.append("Increased complexity for hero asset")

        # Build texture requirements
        required_textures = template["required_textures"].copy()
        optional_textures = template["optional_textures"].copy()

        # Adjust based on performance priority
        if performance_priority == "performance":
            # Move some optional textures to a "skip" list
            if TextureType.AO in optional_textures:
                optional_textures.remove(TextureType.AO)
                performance_notes.append("AO can be baked into albedo for performance")

        # Determine texture resolutions
        resolution_key = asset_category
        if is_hero_asset and asset_category in ["character", "weapon", "environment"]:
            resolution_key = f"{asset_category}_hero"
        elif asset_category in ["character", "weapon", "environment"]:
            resolution_key = f"{asset_category}_standard"

        texture_resolutions = self.resolution_guidelines.get(
            resolution_key,
            {tex: 1024 for tex in required_textures}  # Default 1K
        )

        # Adjust resolutions for performance
        if performance_priority == "performance":
            texture_resolutions = {
                tex: min(res, 1024)
                for tex, res in texture_resolutions.items()
            }
            performance_notes.append("Capped textures at 1024 for performance")
        elif performance_priority == "quality" and is_hero_asset:
            texture_resolutions = {
                tex: min(res * 2, 4096)
                for tex, res in texture_resolutions.items()
            }
            reasoning_parts.append("Increased texture resolution for quality")

        # Select shader
        shader_name, engine_settings = self._select_shader(
            engine,
            asset_category,
            template["shader_features"],
            complexity
        )

        # Build suggested parameters
        suggested_params = template["default_params"].copy()

        # Apply custom requirements
        if custom_requirements:
            if "metallic" in custom_requirements:
                suggested_params["metallic_scale"] = custom_requirements["metallic"]
            if "roughness" in custom_requirements:
                suggested_params["roughness_scale"] = custom_requirements["roughness"]

        # Calculate confidence
        confidence = self._calculate_confidence(
            asset_category,
            template,
            engine,
            custom_requirements
        )

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else f"Standard {asset_category} material setup"

        # Track decision
        decision = AgentDecision(
            action="SUGGEST_MATERIAL",
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                "asset_category": asset_category,
                "engine": engine,
                "complexity": complexity.value,
                "shader": shader_name,
            }
        )
        self.record_decision(decision)

        return MaterialSuggestion(
            material_type=template.get("material_type", "Standard PBR"),
            shader_name=shader_name,
            complexity=complexity,
            required_textures=required_textures,
            optional_textures=optional_textures,
            texture_resolutions=texture_resolutions,
            suggested_params=suggested_params,
            engine_settings=engine_settings,
            confidence=confidence,
            reasoning=reasoning,
            performance_notes=performance_notes,
        )

    def _select_shader(
        self,
        engine: str,
        asset_category: str,
        features: List[str],
        complexity: MaterialComplexity
    ) -> tuple[str, Dict[str, Any]]:
        """Select optimal shader for requirements"""
        engine_config = self.engine_shaders.get(engine, {})

        # Special cases
        if asset_category == "vfx":
            if engine == "unity":
                return "Unlit/Transparent", {"rendering_mode": "Transparent"}
            elif engine == "unreal":
                return "Unlit", {"blend_mode": "Translucent"}

        # Character with subsurface
        if asset_category == "character" and "subsurface_scattering" in features:
            if engine == "unity":
                shader = engine_config.get("hdrp_lit", engine_config.get("urp_lit"))
                return shader["shader"], {"subsurface": True}
            elif engine == "unreal":
                shader = engine_config["subsurface"]
                return shader["shader"], shader

        # Default: Use standard PBR
        if engine == "unity":
            shader = engine_config.get("urp_lit", engine_config.get("standard_pbr"))
        elif engine == "unreal":
            shader = engine_config["default_lit"]
        elif engine == "godot":
            shader = engine_config["standard_material_3d"]
        else:
            return "Standard PBR", {}

        return shader["shader"], shader.get("features", {})

    def _calculate_confidence(
        self,
        asset_category: str,
        template: Dict[str, Any],
        engine: str,
        custom_requirements: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate confidence in suggestion"""
        confidence = 0.7  # Base confidence

        # Known category = higher confidence
        if asset_category in self.material_templates:
            confidence += 0.15

        # Known engine = higher confidence
        if engine in self.engine_shaders:
            confidence += 0.10

        # Custom requirements = slightly lower confidence (more unknowns)
        if custom_requirements:
            confidence -= 0.05

        return min(max(confidence, 0.0), 1.0)

    def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """
        Make decision (required by BaseAgent).
        For Material Suggester, the decision is made in suggest_material().
        """
        asset_category = context.get("asset_category", "environment")
        target_engine = context.get("target_engine")
        is_hero = context.get("is_hero_asset", False)

        suggestion = self.suggest_material(
            asset_category,
            target_engine=target_engine,
            is_hero_asset=is_hero
        )

        return AgentDecision(
            action="SUGGEST_MATERIAL",
            confidence=suggestion.confidence,
            reasoning=suggestion.reasoning,
            metadata={
                "shader": suggestion.shader_name,
                "required_textures": [t.value for t in suggestion.required_textures],
                "complexity": suggestion.complexity.value,
            },
            escalation_reason=EscalationReason.LOW_CONFIDENCE if suggestion.confidence < self.confidence_threshold else None,
        )

    def calculate_confidence(
        self,
        context: Dict[str, Any],
        proposed_action: str
    ) -> float:
        """Calculate confidence for proposed action"""
        return self._calculate_confidence(
            asset_category=context.get("asset_category", "environment"),
            template=self.material_templates.get(
                context.get("asset_category", "environment"),
                {}
            ),
            engine=context.get("target_engine", self.default_engine),
            custom_requirements=context.get("custom_requirements"),
        )
