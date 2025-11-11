"""
Test SDXL Generator - Verify it works without GGUF dependencies

This uses the diffusers library which works on Windows without C++ build tools.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vaultmind_forge.forge_diffusion.sdxl_generator import SDXLGenerator
from vaultmind_forge.forge_diffusion.generator import GenerationConfig


def test_sdxl():
    """Test SDXL image generation"""
    print("="*60)
    print("Testing SDXL Generator")
    print("="*60)
    print()

    try:
        # Create generator
        print("Creating SDXL generator...")
        generator = SDXLGenerator(
            model_id="stabilityai/stable-diffusion-xl-base-1.0",
            device="cuda",  # Will fall back to CPU if no CUDA
        )

        print(f"Generator: {generator}")
        print()

        # Initialize (downloads model if needed)
        print("Initializing SDXL (may download models first time)...")
        print("This may take a few minutes on first run...")
        generator.initialize()

        print(f"[OK] SDXL initialized successfully!")
        print(f"Available: {generator.is_available()}")
        print()

        # Create simple test config
        print("Testing generation with simple prompt...")
        config = GenerationConfig(
            prompt="a cute robot, digital art",
            negative_prompt="blurry, low quality",
            width=512,   # Small size for quick test
            height=512,
            num_inference_steps=20,  # Few steps for speed
            batch_size=1,
        )

        print(f"Prompt: {config.prompt}")
        print(f"Size: {config.width}x{config.height}")
        print(f"Steps: {config.num_inference_steps}")
        print()

        # Generate
        print("Generating image...")
        result = generator.generate(config)

        print(f"[OK] Generation completed!")
        print(f"Time: {result.generation_time:.2f}s")
        print(f"Seed: {result.seed}")
        print(f"Images: {len(result.images)}")
        print()

        # Save result
        output_path = Path(__file__).parent / "test_output"
        output_path.mkdir(exist_ok=True)

        image_file = output_path / "sdxl_test.png"
        result.images[0].save(image_file)

        print(f"[OK] Image saved to: {image_file}")
        print()

        # Get stats
        stats = generator.get_stats()
        print("Generator Stats:")
        print(f"  Model: {stats['model_id']}")
        print(f"  Device: {stats['device']}")
        print(f"  Generations: {stats['generation_count']}")
        print()

        print("="*60)
        print("[SUCCESS] SDXL test passed!")
        print("="*60)
        return True

    except Exception as e:
        print(f"[FAIL] SDXL test failed: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_sdxl()
    sys.exit(0 if success else 1)
