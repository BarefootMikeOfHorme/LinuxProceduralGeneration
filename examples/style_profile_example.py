"""
Style Profile System - Practical Usage Examples

Shows how to use style profiles for:
- Auto-detecting style from prompts
- Getting optimized generation parameters
- Style-aware quality checking
- Complete generation pipelines
"""

import sys
from pathlib import Path

# Add vaultmind_forge to path
sys.path.insert(0, str(Path(__file__).parents[1] / "vaultmind_forge"))

from forge_agents import (
    StyleProfileManager,
    create_style_aware_pipeline,
    quick_style_detection,
    get_recommended_params,
    get_profile,
    ALL_PROFILES,
)


def example_1_auto_detection():
    """Example 1: Auto-detect style from prompts"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Auto-Detect Style from Prompts")
    print("="*70)

    test_prompts = [
        "a beautiful anime girl with long hair, manga style",
        "photorealistic portrait, 8k, ray tracing, cinematic lighting",
        "fantasy game character, stylized, world of warcraft style",
        "pixel art sprite, 16-bit, retro game character",
        "creepy horror monster, dark gothic atmosphere",
        "oil painting of a landscape, impressionist, brush strokes",
    ]

    for prompt in test_prompts:
        detected_style = quick_style_detection(prompt)
        print(f"\nPrompt: {prompt[:60]}...")
        print(f"[OK] Detected style: {detected_style}")


def example_2_get_params():
    """Example 2: Get optimized parameters for each style"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Get Optimized Generation Parameters")
    print("="*70)

    styles = ["photorealistic", "anime", "fantasy_game", "pixel_art"]

    for style_name in styles:
        params = get_recommended_params(style_name, output_type="character")

        print(f"\n{style_name.upper()} Style Parameters:")
        print(f"  Steps: {params['steps']}")
        print(f"  CFG Scale: {params['cfg_scale']}")
        print(f"  Sampler: {params['sampler']}")
        print(f"  Clip Skip: {params.get('clip_skip', 1)}")
        if params.get('enable_hires_fix'):
            print(f"  Hires Fix: Enabled")


def example_3_style_aware_guardian():
    """Example 3: Create style-aware Quality Guardian"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Style-Aware Quality Guardian")
    print("="*70)

    manager = StyleProfileManager()

    # Different styles have different quality expectations
    styles_to_test = [
        ("photorealistic", 0.78),  # Very strict
        ("anime", 0.68),           # More lenient on anatomy
        ("pixel_art", 0.60),       # Very lenient (intentionally low-res)
    ]

    for style_name, expected_threshold in styles_to_test:
        profile = get_profile(style_name)
        guardian = manager.create_style_aware_guardian(profile)

        print(f"\n{style_name.upper()} Guardian:")
        print(f"  Min quality threshold: {guardian.min_quality_threshold:.2f}")
        print(f"  Expected: {expected_threshold:.2f}")
        print(f"  [OK] Configured for {profile.name} style")


def example_4_prompt_enhancement():
    """Example 4: Enhance prompts with style-specific keywords"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Prompt Enhancement")
    print("="*70)

    manager = StyleProfileManager()

    test_cases = [
        ("a warrior", "fantasy_game", "high"),
        ("a girl", "anime", "ultra"),
        ("a sword", "pixel_art", "standard"),
    ]

    for prompt, style_name, quality_level in test_cases:
        profile = get_profile(style_name)
        enhanced = manager.enhance_prompt(prompt, profile, quality_level)

        print(f"\nOriginal: {prompt}")
        print(f"Style: {style_name} ({quality_level})")
        print(f"Enhanced: {enhanced}")


def example_5_complete_pipeline():
    """Example 5: Complete style-aware generation pipeline"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Complete Style-Aware Pipeline")
    print("="*70)

    test_prompts = [
        "anime magical girl, sparkles",
        "photorealistic medieval knight in armor",
        "pixel art zombie sprite",
    ]

    for prompt in test_prompts:
        print(f"\n{'─'*70}")
        print(f"Prompt: {prompt}")

        # Create complete pipeline
        params, enhanced_prompt, guardian = create_style_aware_pipeline(
            prompt=prompt,
            style=None,  # Auto-detect
            quality_level="high",
            user_params=None,
        )

        print(f"\n[OK] Pipeline created:")
        print(f"  Enhanced prompt: {enhanced_prompt}")
        print(f"  Generation params:")
        print(f"    - Steps: {params['steps']}")
        print(f"    - CFG: {params['cfg_scale']}")
        print(f"    - Sampler: {params['sampler']}")
        print(f"  Quality Guardian threshold: {guardian.min_quality_threshold:.2f}")


def example_6_parameter_validation():
    """Example 6: Validate parameters against style"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Parameter Validation")
    print("="*70)

    manager = StyleProfileManager()

    # Test valid params
    print("\nTesting VALID anime parameters:")
    anime_profile = get_profile("anime")
    valid_params = {
        "steps": 28,
        "cfg_scale": 7.5,
        "clip_skip": 2,
    }
    is_valid, warnings = manager.validate_params_for_style(valid_params, anime_profile)
    print(f"  Valid: {is_valid}")
    if warnings:
        for warning in warnings:
            print(f"  [WARN]️  {warning}")

    # Test invalid params
    print("\nTesting INVALID anime parameters (missing clip_skip):")
    invalid_params = {
        "steps": 28,
        "cfg_scale": 7.5,
        "clip_skip": 1,  # WRONG! Should be 2 for anime
    }
    is_valid, warnings = manager.validate_params_for_style(invalid_params, anime_profile)
    print(f"  Valid: {is_valid}")
    if warnings:
        for warning in warnings:
            print(f"  [WARN]️  {warning}")

    # Test excessive CFG
    print("\nTesting EXCESSIVE CFG (too high):")
    excessive_params = {
        "steps": 30,
        "cfg_scale": 18.0,  # Way too high!
    }
    photo_profile = get_profile("photorealistic")
    is_valid, warnings = manager.validate_params_for_style(excessive_params, photo_profile)
    print(f"  Valid: {is_valid}")
    if warnings:
        for warning in warnings:
            print(f"  [WARN]️  {warning}")


def example_7_generation_with_retry():
    """Example 7: Generation pipeline with retry logic"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Generation with Retry Logic")
    print("="*70)

    manager = StyleProfileManager()

    prompt = "fantasy hero character, epic armor"
    profile = manager.detect_style(prompt)

    print(f"Prompt: {prompt}")
    print(f"Detected style: {profile.name}\n")

    # Simulate generation attempts with increasing parameters
    for attempt in range(1, 4):
        params = manager.get_optimized_params(
            profile,
            output_type="character",
            attempt_num=attempt
        )

        print(f"Attempt {attempt}:")
        print(f"  Steps: {params['steps']} (increasing on retry)")
        print(f"  CFG: {params['cfg_scale']} (increasing on retry)")

        # In real usage, you would generate here and check quality
        # If quality is good, break; otherwise continue to next attempt


def example_8_user_overrides():
    """Example 8: User parameter overrides"""
    print("\n" + "="*70)
    print("EXAMPLE 8: User Parameter Overrides")
    print("="*70)

    manager = StyleProfileManager()
    profile = get_profile("photorealistic")

    # User wants specific settings
    user_overrides = {
        "steps": 40,      # More steps than default
        "cfg_scale": 9.0, # Higher CFG
    }

    print("Default parameters:")
    default_params = manager.get_optimized_params(profile)
    print(f"  Steps: {default_params['steps']}")
    print(f"  CFG: {default_params['cfg_scale']}")

    print("\nWith user overrides:")
    custom_params = manager.get_optimized_params(
        profile,
        user_overrides=user_overrides
    )
    print(f"  Steps: {custom_params['steps']} (user override)")
    print(f"  CFG: {custom_params['cfg_scale']} (user override)")

    # Validate overrides
    is_valid, warnings = manager.validate_params_for_style(custom_params, profile)
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  [WARN]️  {warning}")
    else:
        print("\n[OK] All overrides within valid ranges")


def example_9_all_profiles_overview():
    """Example 9: Overview of all available profiles"""
    print("\n" + "="*70)
    print("EXAMPLE 9: All Available Style Profiles")
    print("="*70)

    for style_name, profile in ALL_PROFILES.items():
        print(f"\n{style_name.upper()}:")
        print(f"  Description: {profile.description}")
        print(f"  Default steps: {profile.generation_params['steps']}")
        print(f"  Default CFG: {profile.generation_params['cfg_scale']}")
        print(f"  Min quality: {profile.quality_thresholds.get('min_overall_quality', 0.7):.2f}")
        print(f"  Style keywords: {', '.join(profile.style_keywords[:3])}")


def example_10_integration_simulation():
    """Example 10: Simulated complete generation workflow"""
    print("\n" + "="*70)
    print("EXAMPLE 10: Complete Generation Workflow Simulation")
    print("="*70)

    def simulate_generation_workflow(prompt: str, output_path: Path):
        """Simulate complete workflow from prompt to validated asset"""

        print(f"\n{'='*60}")
        print(f"WORKFLOW: '{prompt}'")
        print(f"{'='*60}")

        # Step 1: Create pipeline
        params, enhanced_prompt, guardian = create_style_aware_pipeline(
            prompt=prompt,
            quality_level="high"
        )

        print(f"\n[1] Pipeline Created")
        print(f"    Enhanced: {enhanced_prompt}")
        print(f"    Steps: {params['steps']}, CFG: {params['cfg_scale']}")

        # Step 2: Generate (simulated)
        print(f"\n[2] Generating asset...")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create dummy image
        from PIL import Image
        img = Image.new('RGB', (512, 512), color=(150, 150, 150))
        img.save(output_path)
        print(f"    [OK] Generated: {output_path}")

        # Step 3: Quality Guardian checks
        print(f"\n[3] Quality Guardian assessing...")
        report = guardian.assess_and_fix(output_path)

        print(f"    Quality: {report.overall_quality:.3f}")
        print(f"    Fixes applied: {len(report.fixes_applied)}")

        if report.escalated:
            print(f"    [WARN]️  Escalated: {report.escalation_reason}")
            return "RETRY"
        else:
            print(f"    [OK] Approved!")
            return "SUCCESS"

    # Test workflow with different prompts
    test_prompts = [
        "anime magical girl",
        "photorealistic dragon",
        "pixel art castle",
    ]

    for i, prompt in enumerate(test_prompts):
        output_path = Path(f"output/workflow_test/asset_{i}.png")
        result = simulate_generation_workflow(prompt, output_path)


def main():
    """Run all examples"""
    print("="*80)
    print("STYLE PROFILE SYSTEM - PRACTICAL EXAMPLES")
    print("="*80)

    examples = [
        ("Auto-Detection", example_1_auto_detection),
        ("Get Parameters", example_2_get_params),
        ("Style-Aware Guardian", example_3_style_aware_guardian),
        ("Prompt Enhancement", example_4_prompt_enhancement),
        ("Complete Pipeline", example_5_complete_pipeline),
        ("Parameter Validation", example_6_parameter_validation),
        ("Generation with Retry", example_7_generation_with_retry),
        ("User Overrides", example_8_user_overrides),
        ("All Profiles Overview", example_9_all_profiles_overview),
        ("Integration Simulation", example_10_integration_simulation),
    ]

    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n[ERROR] Example '{name}' failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("EXAMPLES COMPLETED")
    print("="*80)
    print("\n[OK] Style Profile System is ready to use!")
    print("\nKey Features:")
    print("  • Auto-detects style from prompts (anime, photorealistic, etc.)")
    print("  • Research-backed generation parameters per style")
    print("  • Style-aware quality checking (different standards per style)")
    print("  • User-tunable parameter ranges with validation")
    print("  • Prompt enhancement with style keywords")
    print("  • Retry logic with parameter adjustment")
    print("  • Complete integration with Quality Guardian")
    print("\nNext Steps:")
    print("  • Try: from forge_agents import create_style_aware_pipeline")
    print("  • Use in your generation pipeline for automatic style handling")
    print("  • Customize profiles in style_profiles.py for your models")


if __name__ == "__main__":
    main()
