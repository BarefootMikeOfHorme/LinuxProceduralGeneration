#!/usr/bin/env python3
"""
Test Real SDXL Generation
Quick test to verify SDXL pipeline works
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from vaultmind_forge.forge_diffusion.generator import (
    DiffusionGenerator,
    GenerationConfig,
    GenerationBackend
)

def test_sdxl_turbo():
    """Test SDXL Turbo (fastest for testing)"""
    print("=" * 60)
    print("Testing Real SDXL Generation")
    print("=" * 60)
    print()

    # Create generator with SDXL Turbo (faster)
    print("Step 1: Initializing SDXL Turbo...")
    generator = DiffusionGenerator(
        backend=GenerationBackend.SDXL_TURBO,
        device="cuda" if __import__("torch").cuda.is_available() else "cpu"
    )

    # Load models (will download ~7GB on first run)
    print("Step 2: Loading models (this may take a few minutes on first run)...")
    print("         Downloading from Hugging Face if needed...")
    generator.load_models(
        enable_xformers=True,
        enable_attention_slicing=True
    )

    # Create generation config
    print()
    print("Step 3: Configuring generation...")
    config = GenerationConfig(
        prompt="california girl at the beach tanning in her shades sipping a mai tai in her bikini, highly detailed, photorealistic",
        width=512,  # Smaller for faster testing
        height=512,
        steps=4,  # SDXL Turbo works well with 4 steps!
        guidance_scale=0.0,  # Turbo doesn't use guidance
        batch_size=1
    )

    print(f"  Prompt: {config.prompt}")
    print(f"  Size: {config.width}x{config.height}")
    print(f"  Steps: {config.steps}")
    print()

    # Generate
    print("Step 4: Generating image...")
    result = generator.generate(config)

    # Save result
    output_path = Path("output_real_sdxl.png")
    result.images[0].save(output_path)

    print()
    print("=" * 60)
    print(f"SUCCESS! Image saved to: {output_path.absolute()}")
    print(f"Generation time: {result.generation_time:.2f}s")
    print(f"Seed: {result.seed}")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_sdxl_turbo()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
