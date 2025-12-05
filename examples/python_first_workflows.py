"""
VaultMind Forge - Python-First Workflow Examples
Demonstrates using Python API directly without Web UI

All examples work standalone - no FastAPI or Web UI needed!
"""

import sys
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# EXAMPLE 1: Simple Image Generation
# ============================================================================

def example_1_simple_generation():
    """
    Simplest example: Generate one image with SDXL

    NO WEB UI NEEDED - Pure Python!
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Simple SDXL Generation")
    print("="*60)

    from vaultmind_forge.forge_diffusion import SDXLGenerator
    from vaultmind_forge.forge_diffusion.generator import GenerationConfig

    # Initialize generator (downloads model on first run)
    print("\n[1/3] Initializing SDXL...")
    generator = SDXLGenerator()
    generator.initialize()

    # Configure generation
    print("[2/3] Configuring generation...")
    config = GenerationConfig(
        prompt="fantasy warrior with detailed armor",
        width=1024,
        height=1024,
        steps=30,
        guidance_scale=7.5
    )

    # Generate!
    print("[3/3] Generating image...")
    result = generator.generate(config)

    # Save
    output_path = PROJECT_ROOT / "output" / "example1_simple.png"
    output_path.parent.mkdir(exist_ok=True)
    result.images[0].save(output_path)

    print(f"\n✅ Generated: {output_path}")
    print(f"   Seed: {result.seed}")
    print(f"   Time: {result.generation_time:.2f}s")


# ============================================================================
# EXAMPLE 2: Multi-Pass Generation with Quality Selection
# ============================================================================

def example_2_multipass_generation():
    """
    Advanced: Generate multiple variants and auto-select best

    This is the POWER of Python - complex logic easily!
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Multi-Pass Generation")
    print("="*60)

    from vaultmind_forge.forge_diffusion import SDXLGenerator
    from vaultmind_forge.forge_diffusion.generator import GenerationConfig
    from vaultmind_forge.forge_validator.metrics import compute_metrics

    # Initialize
    print("\n[1/5] Initializing SDXL...")
    generator = SDXLGenerator()
    generator.initialize()

    # Generate 3 variants
    print("[2/5] Generating 3 variants...")
    prompt = "cyberpunk cityscape at night"
    variants = []

    for i in range(3):
        config = GenerationConfig(
            prompt=prompt,
            width=1024,
            height=1024,
            steps=30,
            seed=None  # Random seed for variety
        )

        print(f"   Generating variant {i+1}/3...")
        result = generator.generate(config)
        variants.append({
            'image': result.images[0],
            'seed': result.seed,
            'index': i
        })

    # Validate all variants
    print("[3/5] Computing quality scores...")
    for variant in variants:
        # Convert PIL to numpy for validation
        import numpy as np
        img_array = np.array(variant['image'])

        # Compute metrics
        metrics = compute_metrics(img_array)
        variant['quality'] = metrics
        variant['score'] = (
            metrics.sharpness * 0.4 +
            metrics.color_fidelity * 0.3 +
            metrics.contrast * 0.3
        )

        print(f"   Variant {variant['index']+1}: Score={variant['score']:.3f} "
              f"(sharp={metrics.sharpness:.2f}, color={metrics.color_fidelity:.2f})")

    # Select best
    print("[4/5] Selecting winner...")
    winner = max(variants, key=lambda x: x['score'])
    print(f"   Winner: Variant {winner['index']+1} (Score: {winner['score']:.3f})")

    # Save best
    print("[5/5] Saving winner...")
    output_path = PROJECT_ROOT / "output" / "example2_best.png"
    output_path.parent.mkdir(exist_ok=True)
    winner['image'].save(output_path)

    print(f"\n✅ Best image saved: {output_path}")
    print(f"   Seed: {winner['seed']}")
    print(f"   Quality metrics:")
    print(f"     Sharpness: {winner['quality'].sharpness:.3f}")
    print(f"     Color Fidelity: {winner['quality'].color_fidelity:.3f}")
    print(f"     Contrast: {winner['quality'].contrast:.3f}")


# ============================================================================
# EXAMPLE 3: Full Pipeline (Generate → Validate → Upscale)
# ============================================================================

def example_3_full_pipeline():
    """
    Complete pipeline: Generate → Validate → Upscale if good

    Shows Python orchestration of multiple modules
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Full Pipeline")
    print("="*60)

    from vaultmind_forge.forge_diffusion import SDXLGenerator
    from vaultmind_forge.forge_diffusion.generator import GenerationConfig
    from vaultmind_forge.forge_validator.metrics import compute_metrics
    from vaultmind_forge.forge_sr import RealESRGANUpscaler
    import numpy as np

    # Step 1: Generate
    print("\n[1/4] Generating image...")
    generator = SDXLGenerator()
    generator.initialize()

    config = GenerationConfig(
        prompt="majestic dragon in mountains",
        width=512,  # Lower res for speed
        height=512,
        steps=20
    )

    result = generator.generate(config)
    base_image = result.images[0]

    # Step 2: Validate
    print("[2/4] Validating quality...")
    img_array = np.array(base_image)
    metrics = compute_metrics(img_array)
    quality_score = (metrics.sharpness + metrics.color_fidelity + metrics.contrast) / 3

    print(f"   Quality Score: {quality_score:.3f}")
    print(f"   Sharpness: {metrics.sharpness:.3f}")
    print(f"   Color: {metrics.color_fidelity:.3f}")
    print(f"   Contrast: {metrics.contrast:.3f}")

    # Step 3: Decide based on quality
    QUALITY_THRESHOLD = 0.7

    if quality_score >= QUALITY_THRESHOLD:
        print(f"[3/4] Quality PASSED (>{QUALITY_THRESHOLD}) - Upscaling...")

        # Upscale
        try:
            upscaler = RealESRGANUpscaler()
            upscaled = upscaler.upscale(base_image, scale=4)

            # Save upscaled
            output_path = PROJECT_ROOT / "output" / "example3_upscaled.png"
            output_path.parent.mkdir(exist_ok=True)
            upscaled.save(output_path)

            print(f"[4/4] Saved upscaled: {output_path}")
            print(f"\n✅ Pipeline complete!")
            print(f"   Original: 512x512")
            print(f"   Upscaled: {upscaled.width}x{upscaled.height}")

        except Exception as e:
            print(f"[3/4] Upscaling failed: {e}")
            print(f"[4/4] Saving base image instead...")
            output_path = PROJECT_ROOT / "output" / "example3_base.png"
            output_path.parent.mkdir(exist_ok=True)
            base_image.save(output_path)
            print(f"\n⚠️  Pipeline complete (upscaling unavailable)")
            print(f"   Saved: {output_path}")
    else:
        print(f"[3/4] Quality FAILED (<{QUALITY_THRESHOLD}) - Skipping upscale")
        print(f"[4/4] Saving base image...")
        output_path = PROJECT_ROOT / "output" / "example3_rejected.png"
        output_path.parent.mkdir(exist_ok=True)
        base_image.save(output_path)

        print(f"\n❌ Quality too low - not upscaled")
        print(f"   Saved: {output_path}")


# ============================================================================
# EXAMPLE 4: Rust Validator Integration
# ============================================================================

def example_4_rust_validators():
    """
    Demonstrate calling Rust validators from Python

    Shows multi-language integration: Python orchestrates, Rust validates
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Rust Validator Integration")
    print("="*60)

    from PIL import Image
    import numpy as np

    # Create test image
    print("\n[1/3] Creating test image...")
    test_image = Image.new('RGB', (512, 512), color='red')
    test_path = PROJECT_ROOT / "output" / "test_texture.png"
    test_path.parent.mkdir(exist_ok=True)
    test_image.save(test_path)
    print(f"   Created: {test_path}")

    # Try to use Rust validators
    print("[2/3] Attempting to load Rust validators...")

    try:
        # Try importing Rust module
        from vaultmind_forge.native.rust.validator import pbr_validator

        print("   ✅ Rust validators loaded!")

        # Use Rust validator
        print("[3/3] Running PBR validation (Rust)...")
        result = pbr_validator.validate_pbr_material(str(test_path))

        print(f"\n✅ Rust validation complete!")
        print(f"   Result: {result}")

    except ImportError as e:
        print(f"   ⚠️  Rust validators not built: {e}")
        print(f"\n[3/3] Falling back to Python validators...")

        # Use Python validator instead
        from vaultmind_forge.forge_validator.metrics import compute_metrics

        img_array = np.array(test_image)
        metrics = compute_metrics(img_array)

        print(f"\n✅ Python validation complete!")
        print(f"   Sharpness: {metrics.sharpness:.3f}")
        print(f"   Color: {metrics.color_fidelity:.3f}")
        print(f"   Contrast: {metrics.contrast:.3f}")

        print(f"\n💡 To enable Rust validators:")
        print(f"   cd vaultmind_forge/native/rust/validator")
        print(f"   cargo build --release")
        print(f"   maturin develop --release")


# ============================================================================
# EXAMPLE 5: Lineage Tracking
# ============================================================================

def example_5_lineage_tracking():
    """
    Track asset lineage in pure Python

    Every asset gets complete provenance
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Lineage Tracking")
    print("="*60)

    from vaultmind_forge.forge_lineage import LineageLogger
    from vaultmind_forge.forge_diffusion import SDXLGenerator
    from vaultmind_forge.forge_diffusion.generator import GenerationConfig
    import json

    # Create lineage logger
    print("\n[1/4] Initializing lineage tracker...")
    lineage_dir = PROJECT_ROOT / "output" / "lineage"
    lineage_dir.mkdir(parents=True, exist_ok=True)
    logger = LineageLogger(str(lineage_dir))

    # Generate with lineage
    print("[2/4] Generating with lineage tracking...")
    generator = SDXLGenerator()
    generator.initialize()

    config = GenerationConfig(
        prompt="ancient temple ruins",
        width=512,
        height=512,
        steps=15
    )

    # Start lineage record
    job_id = "example5_lineage"
    logger.log_job_start(job_id, {
        'prompt': config.prompt,
        'width': config.width,
        'height': config.height,
        'steps': config.steps,
    })

    # Generate
    result = generator.generate(config)

    # Save with lineage
    print("[3/4] Saving with lineage...")
    output_path = PROJECT_ROOT / "output" / "example5_lineage.png"
    output_path.parent.mkdir(exist_ok=True)
    result.images[0].save(output_path)

    # Complete lineage
    logger.log_asset_created(job_id, str(output_path), {
        'seed': result.seed,
        'generation_time': result.generation_time,
    })

    logger.log_job_complete(job_id)

    # Read back lineage
    print("[4/4] Reading lineage record...")
    lineage_file = lineage_dir / f"{job_id}.json"

    if lineage_file.exists():
        with open(lineage_file) as f:
            lineage = json.load(f)

        print(f"\n✅ Lineage tracked!")
        print(f"   Job ID: {lineage.get('job_id')}")
        print(f"   Timestamp: {lineage.get('timestamp')}")
        print(f"   Config: {lineage.get('config')}")
        print(f"   Asset: {lineage.get('assets', [{}])[0].get('path')}")
        print(f"   Lineage file: {lineage_file}")
    else:
        print(f"\n⚠️  Lineage file not found: {lineage_file}")


# ============================================================================
# EXAMPLE 6: Batch Processing
# ============================================================================

def example_6_batch_processing():
    """
    Process multiple prompts in batch

    Shows Python's power for automation
    """
    print("\n" + "="*60)
    print("EXAMPLE 6: Batch Processing")
    print("="*60)

    from vaultmind_forge.forge_diffusion import SDXLGenerator
    from vaultmind_forge.forge_diffusion.generator import GenerationConfig

    # Batch of prompts
    prompts = [
        "sunset over ocean",
        "mountain landscape",
        "forest path",
    ]

    print(f"\n[1/3] Processing {len(prompts)} prompts...")

    # Initialize once
    generator = SDXLGenerator()
    generator.initialize()

    # Process batch
    print("[2/3] Generating batch...")
    results = []

    for i, prompt in enumerate(prompts, 1):
        print(f"   Generating {i}/{len(prompts)}: {prompt}...")

        config = GenerationConfig(
            prompt=prompt,
            width=512,
            height=512,
            steps=15  # Fast
        )

        result = generator.generate(config)

        # Save
        filename = prompt.replace(" ", "_")[:30]
        output_path = PROJECT_ROOT / "output" / "batch" / f"{i}_{filename}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.images[0].save(output_path)

        results.append({
            'prompt': prompt,
            'path': output_path,
            'seed': result.seed,
            'time': result.generation_time
        })

    # Summary
    print("[3/3] Batch complete!")
    print(f"\n✅ Generated {len(results)} images:")

    total_time = sum(r['time'] for r in results)
    for r in results:
        print(f"   • {r['path'].name}")
        print(f"     Prompt: {r['prompt']}")
        print(f"     Time: {r['time']:.1f}s")

    print(f"\n   Total time: {total_time:.1f}s")
    print(f"   Average: {total_time/len(results):.1f}s per image")


# ============================================================================
# MAIN - Run All Examples
# ============================================================================

def main():
    """Run examples based on user choice"""
    print("\n" + "="*60)
    print("VaultMind Forge - Python-First Workflow Examples")
    print("="*60)
    print("\nDemonstrating Python API WITHOUT Web UI!")
    print("\nAvailable examples:")
    print("  1. Simple SDXL generation")
    print("  2. Multi-pass generation with quality selection")
    print("  3. Full pipeline (Generate → Validate → Upscale)")
    print("  4. Rust validator integration")
    print("  5. Lineage tracking")
    print("  6. Batch processing")
    print("  0. Run all (sequential)")

    choice = input("\nSelect example (0-6): ").strip()

    examples = {
        '1': example_1_simple_generation,
        '2': example_2_multipass_generation,
        '3': example_3_full_pipeline,
        '4': example_4_rust_validators,
        '5': example_5_lineage_tracking,
        '6': example_6_batch_processing,
    }

    if choice == '0':
        print("\n🚀 Running all examples...")
        for num, func in examples.items():
            try:
                func()
            except Exception as e:
                print(f"\n❌ Example {num} failed: {e}")
                import traceback
                traceback.print_exc()
    elif choice in examples:
        try:
            examples[choice]()
        except Exception as e:
            print(f"\n❌ Example failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Invalid choice!")

    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60)


if __name__ == "__main__":
    main()
