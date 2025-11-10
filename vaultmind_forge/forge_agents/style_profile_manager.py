"""
StyleProfileManager - Manages style profiles and auto-detection

This manager:
- Auto-detects style from prompts
- Integrates profiles with Quality Guardian
- Optimizes generation parameters per style
- Provides style-aware quality checking
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List
import re
import logging

from .style_profiles import (
    StyleProfile,
    ALL_PROFILES,
    PROFILE_ALIASES,
    get_profile,
    PHOTOREALISTIC_PROFILE,
    ANIME_PROFILE,
    FANTASY_GAME_PROFILE,
    PIXEL_ART_PROFILE,
    HORROR_PROFILE,
    PAINTERLY_PROFILE,
)

logger = logging.getLogger(__name__)


class StyleProfileManager:
    """
    Manages style profiles for generation and quality checking.

    Capabilities:
    - Auto-detect style from prompts
    - Apply style-specific quality thresholds
    - Optimize generation parameters per style
    - Integrate with Quality Guardian Agent
    """

    def __init__(
        self,
        default_profile: str = "photorealistic",
        enable_auto_detection: bool = True,
    ):
        """
        Initialize StyleProfileManager.

        Args:
            default_profile: Profile to use when auto-detection fails
            enable_auto_detection: Whether to auto-detect style from prompts
        """
        self.default_profile_name = default_profile
        self.default_profile = get_profile(default_profile)
        self.enable_auto_detection = enable_auto_detection

        # Style detection keywords (ordered by priority)
        self.style_keywords = {
            "anime": [
                r'\banime\b', r'\bmanga\b', r'\bchibi\b', r'\bmoe\b',
                r'\bwaifu\b', r'\bcartoon\b', r'\bcel.?shad', r'\b2d\b',
            ],
            "photorealistic": [
                r'\bphoto\b', r'\brealistic\b', r'\bphotorealistic\b',
                r'\b4k\b', r'\b8k\b', r'\bunreal engine\b', r'\bcinematic\b',
                r'\bray.?trac', r'\bhyper.?realistic\b',
            ],
            "fantasy_game": [
                r'\bgame\s+art\b', r'\bfantasy\b', r'\brpg\b', r'\bmmorpg\b',
                r'\bworld\s+of\s+warcraft\b', r'\bleague\s+of\s+legends\b',
                r'\bstylized\b', r'\bhero\s+art\b', r'\bcharacter\s+design\b',
            ],
            "pixel_art": [
                r'\bpixel\s+art\b', r'\b8.?bit\b', r'\b16.?bit\b',
                r'\bretro\b', r'\bpixelated\b', r'\bsprite\b',
            ],
            "horror": [
                r'\bhorror\b', r'\bcreepy\b', r'\bscary\b', r'\bgothic\b',
                r'\bdark\s+fantasy\b', r'\bnightmare\b', r'\beldritch\b',
                r'\bbody\s+horror\b', r'\bzombie\b', r'\bmonster\b',
            ],
            "painterly": [
                r'\bpainting\b', r'\boil\s+painting\b', r'\bimpressionist\b',
                r'\bbrush\s+strokes\b', r'\bartistic\b', r'\bfine\s+art\b',
                r'\bdigital\s+painting\b', r'\bhand.?painted\b',
            ],
        }

        logger.info(f"StyleProfileManager initialized (default: {default_profile})")

    def detect_style(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> StyleProfile:
        """
        Auto-detect style from prompt and context.

        Args:
            prompt: Generation prompt
            negative_prompt: Negative prompt (optional)
            context: Additional context (asset_type, etc.)

        Returns:
            Detected StyleProfile
        """
        if not self.enable_auto_detection:
            return self.default_profile

        # Combine prompt and context for detection
        text_to_check = prompt.lower()
        if negative_prompt:
            text_to_check += " " + negative_prompt.lower()

        # Check for explicit style tags first (e.g., [style:anime])
        style_tag_match = re.search(r'\[style:(\w+)\]', prompt, re.IGNORECASE)
        if style_tag_match:
            style_name = style_tag_match.group(1).lower()
            profile = get_profile(style_name)
            if profile:
                logger.info(f"Style explicitly tagged: {style_name}")
                return profile

        # Score each style based on keyword matches
        style_scores = {}
        for style_name, keywords in self.style_keywords.items():
            score = 0
            for keyword_pattern in keywords:
                if re.search(keyword_pattern, text_to_check, re.IGNORECASE):
                    score += 1
            style_scores[style_name] = score

        # Get highest scoring style
        if style_scores and max(style_scores.values()) > 0:
            detected_style = max(style_scores, key=style_scores.get)
            profile = get_profile(detected_style)
            logger.info(f"Auto-detected style: {detected_style} (score: {style_scores[detected_style]})")
            return profile

        # Context-based detection
        if context:
            asset_type = context.get("asset_type", "").lower()
            if "pixel" in asset_type or "sprite" in asset_type:
                return get_profile("pixel_art")
            elif "character" in asset_type or "hero" in asset_type:
                return get_profile("fantasy_game")

        # Fallback to default
        logger.debug(f"No style detected, using default: {self.default_profile_name}")
        return self.default_profile

    def get_optimized_params(
        self,
        profile: StyleProfile,
        output_type: str = "texture",
        attempt_num: int = 1,
        user_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get optimized generation parameters for style and context.

        Args:
            profile: Style profile to use
            output_type: Type of output (texture, character, environment, etc.)
            attempt_num: Generation attempt number (higher = more aggressive)
            user_overrides: User-specified parameter overrides

        Returns:
            Optimized generation parameters
        """
        # Start with profile defaults
        params = profile.generation_params.copy()

        # Adjust based on attempt number
        if attempt_num > 1:
            # Increase steps slightly on retries
            if "steps" in profile.tunable_params:
                step_range = profile.tunable_params["steps"]
                current_steps = params.get("steps", step_range.default)
                # Increase by 5 steps per attempt, capped at max
                new_steps = min(current_steps + (attempt_num - 1) * 5, step_range.max)
                params["steps"] = new_steps

            # Slightly increase CFG on retries for more adherence
            if "cfg_scale" in profile.tunable_params:
                cfg_range = profile.tunable_params["cfg_scale"]
                current_cfg = params.get("cfg_scale", cfg_range.default)
                # Increase by 0.5 per attempt, capped at max
                new_cfg = min(current_cfg + (attempt_num - 1) * 0.5, cfg_range.max)
                params["cfg_scale"] = new_cfg

        # Output-type specific adjustments
        if output_type in ["character", "hero"]:
            # Higher quality for characters
            if "steps" in params:
                params["steps"] = min(params["steps"] + 5, 50)
            if profile.name == "photorealistic":
                params["enable_hires_fix"] = True

        elif output_type in ["texture", "material"]:
            # Tileability for textures
            params["enable_seamless"] = True

        elif output_type in ["environment", "background"]:
            # Can use lower steps for backgrounds
            if "steps" in params:
                params["steps"] = max(params["steps"] - 5, 20)

        # Apply user overrides (highest priority)
        if user_overrides:
            for key, value in user_overrides.items():
                # Validate against tunable ranges if available
                if key in profile.tunable_params:
                    param_range = profile.tunable_params[key]
                    if param_range.min <= value <= param_range.max:
                        params[key] = value
                    else:
                        logger.warning(
                            f"User override {key}={value} outside valid range "
                            f"[{param_range.min}, {param_range.max}], clamping"
                        )
                        params[key] = max(param_range.min, min(value, param_range.max))
                else:
                    # Not a tunable param, but allow it anyway
                    params[key] = value

        return params

    def integrate_with_quality_guardian(
        self,
        guardian: 'QualityGuardianAgent',
        profile: StyleProfile,
    ):
        """
        Apply style profile thresholds to Quality Guardian.

        Args:
            guardian: QualityGuardianAgent instance
            profile: StyleProfile to apply
        """
        # Apply quality thresholds from profile
        guardian.min_quality_threshold = profile.quality_thresholds.get(
            "min_overall_quality",
            guardian.min_quality_threshold
        )

        # Store profile reference for style-aware checking
        guardian._style_profile = profile

        logger.info(
            f"Applied {profile.name} profile to Quality Guardian "
            f"(min_quality={guardian.min_quality_threshold:.2f})"
        )

    def create_style_aware_guardian(
        self,
        profile: StyleProfile,
        auto_fix_enabled: bool = True,
        **guardian_kwargs,
    ) -> 'QualityGuardianAgent':
        """
        Create Quality Guardian pre-configured for a specific style.

        Args:
            profile: Style profile to use
            auto_fix_enabled: Enable auto-fixing
            **guardian_kwargs: Additional QualityGuardianAgent arguments

        Returns:
            Configured QualityGuardianAgent
        """
        from .quality_guardian import QualityGuardianAgent

        # Extract quality thresholds from profile
        min_quality = profile.quality_thresholds.get("min_overall_quality", 0.70)

        # Create guardian with style-specific settings
        guardian = QualityGuardianAgent(
            min_quality_threshold=min_quality,
            auto_fix_enabled=auto_fix_enabled,
            **guardian_kwargs
        )

        # Apply full profile integration
        self.integrate_with_quality_guardian(guardian, profile)

        return guardian

    def enhance_prompt(
        self,
        prompt: str,
        profile: StyleProfile,
        quality_level: str = "standard",
    ) -> str:
        """
        Enhance prompt with style-specific keywords.

        Args:
            prompt: Original prompt
            profile: Style profile
            quality_level: Quality level (low, standard, high, ultra)

        Returns:
            Enhanced prompt
        """
        enhanced = prompt

        # Add style keywords if not already present
        keywords_to_add = []
        for keyword in profile.style_keywords[:3]:  # Top 3 keywords
            if keyword.lower() not in enhanced.lower():
                keywords_to_add.append(keyword)

        if keywords_to_add:
            enhanced += ", " + ", ".join(keywords_to_add)

        # Add quality modifiers based on level
        quality_modifiers = {
            "low": [],
            "standard": ["detailed"],
            "high": ["highly detailed", "masterpiece"],
            "ultra": ["highly detailed", "masterpiece", "best quality", "8k"],
        }

        for modifier in quality_modifiers.get(quality_level, []):
            if modifier.lower() not in enhanced.lower():
                enhanced += f", {modifier}"

        return enhanced

    def get_negative_prompt(
        self,
        profile: StyleProfile,
        user_negative: Optional[str] = None,
    ) -> str:
        """
        Get complete negative prompt for style.

        Args:
            profile: Style profile
            user_negative: User-provided negative prompt

        Returns:
            Complete negative prompt
        """
        # Start with profile defaults
        negative = ", ".join(profile.negative_prompt_defaults)

        # Append user negatives
        if user_negative:
            negative += f", {user_negative}"

        return negative

    def validate_params_for_style(
        self,
        params: Dict[str, Any],
        profile: StyleProfile,
    ) -> tuple[bool, List[str]]:
        """
        Validate generation parameters against style profile.

        Args:
            params: Generation parameters to validate
            profile: Style profile to validate against

        Returns:
            (is_valid, warnings) - warnings list contains parameter issues
        """
        warnings = []

        # Check tunable parameters
        for param_name, param_range in profile.tunable_params.items():
            if param_name in params:
                value = params[param_name]
                if value < param_range.min or value > param_range.max:
                    warnings.append(
                        f"{param_name}={value} outside recommended range "
                        f"[{param_range.min}, {param_range.max}] for {profile.name}"
                    )

        # Style-specific validations
        if profile.name.lower() == "anime":
            # Critical: anime models need clip_skip 2
            if params.get("clip_skip", 1) != 2:
                warnings.append(
                    "Anime style requires clip_skip=2 for proper model behavior!"
                )

        if profile.name.lower() == "pixel art":
            # Pixel art shouldn't use hires fix (creates antialiasing)
            if params.get("enable_hires_fix", False):
                warnings.append(
                    "Pixel art should not use hires_fix (causes unwanted antialiasing)"
                )

        # General validations
        if params.get("steps", 20) < 15:
            warnings.append("Steps < 15 may produce low quality results")

        if params.get("cfg_scale", 7) > 15:
            warnings.append("CFG > 15 may cause artifacts and over-saturation")

        is_valid = len(warnings) == 0
        return is_valid, warnings

    def get_profile_for_prompt(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> tuple[StyleProfile, str]:
        """
        Convenience method: detect style and return profile with detection reason.

        Args:
            prompt: Generation prompt
            negative_prompt: Negative prompt
            context: Additional context

        Returns:
            (profile, reason) - StyleProfile and detection reason string
        """
        profile = self.detect_style(prompt, negative_prompt, context)

        # Determine reason
        if profile.name == self.default_profile_name:
            reason = f"default ({self.default_profile_name})"
        else:
            reason = f"auto-detected ({profile.name})"

        return profile, reason


# Convenience functions for common workflows

def create_style_aware_pipeline(
    prompt: str,
    style: Optional[str] = None,
    quality_level: str = "standard",
    user_params: Optional[Dict[str, Any]] = None,
) -> tuple[Dict[str, Any], str, 'QualityGuardianAgent']:
    """
    Create complete style-aware generation pipeline.

    Args:
        prompt: Generation prompt
        style: Style name (or None for auto-detection)
        quality_level: Quality level (low, standard, high, ultra)
        user_params: User parameter overrides

    Returns:
        (generation_params, enhanced_prompt, quality_guardian)
    """
    manager = StyleProfileManager()

    # Get or detect profile
    if style:
        profile = get_profile(style)
        if not profile:
            logger.warning(f"Unknown style '{style}', using default")
            profile = manager.default_profile
    else:
        profile = manager.detect_style(prompt)

    # Get optimized parameters
    params = manager.get_optimized_params(
        profile,
        output_type="texture",
        attempt_num=1,
        user_overrides=user_params,
    )

    # Enhance prompt
    enhanced_prompt = manager.enhance_prompt(prompt, profile, quality_level)

    # Add negative prompt
    params["negative_prompt"] = manager.get_negative_prompt(profile)

    # Create style-aware Quality Guardian
    guardian = manager.create_style_aware_guardian(profile)

    logger.info(f"Pipeline created for {profile.name} style")

    return params, enhanced_prompt, guardian


def quick_style_detection(prompt: str) -> str:
    """
    Quick style detection for a prompt.

    Args:
        prompt: Prompt to analyze

    Returns:
        Detected style name (lowercase key)
    """
    manager = StyleProfileManager()
    profile = manager.detect_style(prompt)

    # Return lowercase key, not capitalized name
    for key, prof in ALL_PROFILES.items():
        if prof.name == profile.name:
            return key

    # Fallback to lowercase name
    return profile.name.lower().replace(" ", "_")


def get_recommended_params(style: str, output_type: str = "texture") -> Dict[str, Any]:
    """
    Get recommended generation parameters for a style.

    Args:
        style: Style name
        output_type: Output type

    Returns:
        Recommended parameters
    """
    profile = get_profile(style)
    if not profile:
        raise ValueError(f"Unknown style: {style}")

    manager = StyleProfileManager()
    return manager.get_optimized_params(profile, output_type)
