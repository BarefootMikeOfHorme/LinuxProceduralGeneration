"""
Tests for Style Profile System

Tests:
1. StyleProfile creation and validation
2. Auto-detection from prompts
3. Parameter optimization
4. Quality Guardian integration
5. Parameter validation
6. Prompt enhancement
"""

import sys
from pathlib import Path
import unittest

# Add parent to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from forge_agents import (
    StyleProfile,
    ParameterRange,
    StyleProfileManager,
    get_profile,
    ALL_PROFILES,
    quick_style_detection,
    get_recommended_params,
    create_style_aware_pipeline,
)


class TestStyleProfiles(unittest.TestCase):
    """Test style profile creation and access"""

    def test_1_profile_exists(self):
        """Test that all expected profiles exist"""
        expected_profiles = [
            "photorealistic",
            "anime",
            "fantasy_game",
            "pixel_art",
            "horror",
            "painterly",
        ]

        for profile_name in expected_profiles:
            profile = get_profile(profile_name)
            self.assertIsNotNone(profile, f"Profile {profile_name} should exist")
            self.assertIsInstance(profile, StyleProfile)

    def test_2_profile_has_required_fields(self):
        """Test that profiles have all required fields"""
        profile = get_profile("photorealistic")

        # Check required fields
        self.assertIsNotNone(profile.name)
        self.assertIsNotNone(profile.description)
        self.assertIsInstance(profile.generation_params, dict)
        self.assertIsInstance(profile.quality_thresholds, dict)
        self.assertIsInstance(profile.tunable_params, dict)
        self.assertIsInstance(profile.style_keywords, list)

        # Check generation params have minimum required
        self.assertIn("steps", profile.generation_params)
        self.assertIn("cfg_scale", profile.generation_params)
        self.assertIn("sampler", profile.generation_params)

    def test_3_parameter_ranges(self):
        """Test ParameterRange validation"""
        profile = get_profile("anime")

        # Check tunable params have ranges
        self.assertIn("steps", profile.tunable_params)
        step_range = profile.tunable_params["steps"]

        self.assertIsInstance(step_range, ParameterRange)
        self.assertLessEqual(step_range.min, step_range.default)
        self.assertLessEqual(step_range.default, step_range.max)

    def test_4_anime_clip_skip(self):
        """Test anime profile has critical clip_skip=2"""
        profile = get_profile("anime")

        self.assertEqual(
            profile.generation_params.get("clip_skip", 1),
            2,
            "Anime profile MUST have clip_skip=2"
        )


class TestStyleDetection(unittest.TestCase):
    """Test auto-detection of styles from prompts"""

    def test_1_detect_anime(self):
        """Test anime style detection"""
        prompts = [
            "anime girl with long hair",
            "manga character, cel shaded",
            "cute chibi character",
        ]

        for prompt in prompts:
            detected = quick_style_detection(prompt)
            self.assertEqual(detected, "anime", f"Should detect anime in: {prompt}")

    def test_2_detect_photorealistic(self):
        """Test photorealistic style detection"""
        prompts = [
            "photorealistic portrait, 8k",
            "realistic render, ray tracing",
            "unreal engine, cinematic",
        ]

        for prompt in prompts:
            detected = quick_style_detection(prompt)
            self.assertEqual(detected, "photorealistic", f"Should detect photorealistic in: {prompt}")

    def test_3_detect_pixel_art(self):
        """Test pixel art style detection"""
        prompts = [
            "pixel art sprite",
            "8-bit retro game",
            "16-bit character",
        ]

        for prompt in prompts:
            detected = quick_style_detection(prompt)
            self.assertEqual(detected, "pixel_art", f"Should detect pixel_art in: {prompt}")

    def test_4_explicit_style_tag(self):
        """Test explicit style tag overrides auto-detection"""
        manager = StyleProfileManager()

        prompt = "a character [style:anime]"
        profile = manager.detect_style(prompt)

        self.assertEqual(profile.name, "Anime", "Explicit tag should override")  # Name is capitalized


class TestParameterOptimization(unittest.TestCase):
    """Test parameter optimization"""

    def test_1_get_recommended_params(self):
        """Test getting recommended params for a style"""
        params = get_recommended_params("photorealistic")

        self.assertIn("steps", params)
        self.assertIn("cfg_scale", params)
        self.assertIn("sampler", params)

        # Check values are reasonable
        self.assertGreaterEqual(params["steps"], 20)
        self.assertLessEqual(params["steps"], 50)

    def test_2_params_increase_on_retry(self):
        """Test parameters increase on retry attempts"""
        manager = StyleProfileManager()
        profile = get_profile("photorealistic")

        # Get params for attempt 1
        params1 = manager.get_optimized_params(profile, attempt_num=1)

        # Get params for attempt 3
        params3 = manager.get_optimized_params(profile, attempt_num=3)

        # Steps and CFG should increase on retries
        self.assertGreater(
            params3["steps"],
            params1["steps"],
            "Steps should increase on retry"
        )
        self.assertGreater(
            params3["cfg_scale"],
            params1["cfg_scale"],
            "CFG should increase on retry"
        )

    def test_3_user_overrides(self):
        """Test user parameter overrides"""
        manager = StyleProfileManager()
        profile = get_profile("anime")

        user_overrides = {
            "steps": 35,
            "cfg_scale": 8.0,
        }

        params = manager.get_optimized_params(
            profile,
            user_overrides=user_overrides
        )

        self.assertEqual(params["steps"], 35)
        self.assertEqual(params["cfg_scale"], 8.0)

    def test_4_output_type_adjustment(self):
        """Test parameters adjust for output type"""
        manager = StyleProfileManager()
        profile = get_profile("photorealistic")

        # Character should get higher quality
        char_params = manager.get_optimized_params(profile, output_type="character")
        bg_params = manager.get_optimized_params(profile, output_type="background")

        self.assertGreaterEqual(
            char_params["steps"],
            bg_params["steps"],
            "Character should get more steps than background"
        )


class TestParameterValidation(unittest.TestCase):
    """Test parameter validation"""

    def test_1_valid_anime_params(self):
        """Test valid anime parameters pass validation"""
        manager = StyleProfileManager()
        profile = get_profile("anime")

        valid_params = {
            "steps": 28,
            "cfg_scale": 7.5,
            "clip_skip": 2,
        }

        is_valid, warnings = manager.validate_params_for_style(valid_params, profile)
        self.assertTrue(is_valid, "Valid params should pass")
        self.assertEqual(len(warnings), 0, "Should have no warnings")

    def test_2_invalid_anime_clip_skip(self):
        """Test invalid clip_skip for anime triggers warning"""
        manager = StyleProfileManager()
        profile = get_profile("anime")

        invalid_params = {
            "steps": 28,
            "cfg_scale": 7.5,
            "clip_skip": 1,  # WRONG! Should be 2
        }

        is_valid, warnings = manager.validate_params_for_style(invalid_params, profile)
        self.assertFalse(is_valid, "Should detect invalid clip_skip")
        self.assertGreater(len(warnings), 0, "Should have warnings")

        # Check warning mentions clip_skip
        warning_text = " ".join(warnings).lower()
        self.assertIn("clip_skip", warning_text)

    def test_3_excessive_cfg(self):
        """Test excessive CFG triggers warning"""
        manager = StyleProfileManager()
        profile = get_profile("photorealistic")

        excessive_params = {
            "steps": 30,
            "cfg_scale": 18.0,  # Way too high!
        }

        is_valid, warnings = manager.validate_params_for_style(excessive_params, profile)
        self.assertFalse(is_valid, "Should detect excessive CFG")
        self.assertGreater(len(warnings), 0, "Should have warnings")

    def test_4_out_of_range(self):
        """Test out-of-range parameters trigger warnings"""
        manager = StyleProfileManager()
        profile = get_profile("photorealistic")

        out_of_range = {
            "steps": 100,  # Way too many
            "cfg_scale": 2.0,  # Way too low
        }

        is_valid, warnings = manager.validate_params_for_style(out_of_range, profile)
        self.assertFalse(is_valid, "Should detect out-of-range params")


class TestQualityGuardianIntegration(unittest.TestCase):
    """Test integration with Quality Guardian"""

    def test_1_create_style_aware_guardian(self):
        """Test creating style-aware Quality Guardian"""
        manager = StyleProfileManager()
        profile = get_profile("anime")

        guardian = manager.create_style_aware_guardian(profile)

        # Check guardian has style profile
        self.assertTrue(hasattr(guardian, "_style_profile"))
        self.assertEqual(guardian._style_profile.name, "Anime")  # Name is capitalized

        # Check threshold was applied
        expected_threshold = profile.quality_thresholds.get("min_overall_quality", 0.7)
        self.assertAlmostEqual(guardian.min_quality_threshold, expected_threshold, places=2)

    def test_2_different_thresholds_per_style(self):
        """Test different styles have different quality thresholds"""
        manager = StyleProfileManager()

        # Photorealistic should be strict
        photo_profile = get_profile("photorealistic")
        photo_guardian = manager.create_style_aware_guardian(photo_profile)

        # Pixel art should be lenient
        pixel_profile = get_profile("pixel_art")
        pixel_guardian = manager.create_style_aware_guardian(pixel_profile)

        self.assertGreater(
            photo_guardian.min_quality_threshold,
            pixel_guardian.min_quality_threshold,
            "Photorealistic should have stricter threshold than pixel art"
        )


class TestPromptEnhancement(unittest.TestCase):
    """Test prompt enhancement"""

    def test_1_enhance_basic_prompt(self):
        """Test enhancing a basic prompt"""
        manager = StyleProfileManager()
        profile = get_profile("anime")

        original = "a girl"
        enhanced = manager.enhance_prompt(original, profile, quality_level="high")

        # Should be longer
        self.assertGreater(len(enhanced), len(original))

        # Should contain original
        self.assertIn(original, enhanced)

    def test_2_quality_level_affects_enhancement(self):
        """Test different quality levels produce different enhancements"""
        manager = StyleProfileManager()
        profile = get_profile("photorealistic")

        prompt = "a portrait"

        low = manager.enhance_prompt(prompt, profile, "low")
        ultra = manager.enhance_prompt(prompt, profile, "ultra")

        # Ultra should be longer/more detailed
        self.assertGreater(len(ultra), len(low))

    def test_3_negative_prompt_generation(self):
        """Test negative prompt generation"""
        manager = StyleProfileManager()
        profile = get_profile("anime")

        negative = manager.get_negative_prompt(profile)

        # Should not be empty
        self.assertGreater(len(negative), 0)

        # Should contain some defaults from profile
        self.assertTrue(any(
            default in negative
            for default in profile.negative_prompt_defaults
        ))


class TestCompletePipeline(unittest.TestCase):
    """Test complete pipeline creation"""

    def test_1_create_pipeline(self):
        """Test creating complete style-aware pipeline"""
        prompt = "anime magical girl"

        params, enhanced_prompt, guardian = create_style_aware_pipeline(
            prompt=prompt,
            quality_level="high"
        )

        # Check we got all components
        self.assertIsInstance(params, dict)
        self.assertIsInstance(enhanced_prompt, str)
        self.assertIsNotNone(guardian)

        # Check params have required fields
        self.assertIn("steps", params)
        self.assertIn("cfg_scale", params)
        self.assertIn("negative_prompt", params)

        # Check prompt was enhanced
        self.assertGreater(len(enhanced_prompt), len(prompt))

    def test_2_explicit_style_override(self):
        """Test explicit style override in pipeline"""
        prompt = "a character"

        params, _, _ = create_style_aware_pipeline(
            prompt=prompt,
            style="pixel_art"  # Explicit override
        )

        # Pixel art should have specific settings
        # (no hires fix, small resolution)
        self.assertFalse(params.get("enable_hires_fix", False))


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n[PASS] ALL TESTS PASSED!")
    else:
        print("\n[FAIL] SOME TESTS FAILED")

    return result


if __name__ == "__main__":
    run_tests()
