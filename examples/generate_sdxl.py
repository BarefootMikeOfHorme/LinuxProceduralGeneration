#!/usr/bin/env python3
"""
VaultMind Forge - SDXL Generation CLI Script

Used by vaultmind_cli.py for the 'generate' command
Generates images using SDXL with complete lineage tracking
"""

import argparse
import sys
from pathlib import Path
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from vaultmind_forge.forge_diffusion.generator import (
        DiffusionGenerator,
        GenerationConfig,
        GenerationBackend
    )
    from vaultmind_forge.forge_lineage.lineage_tracker import LineageTracker
    from vaultmind_forge.forge_validator.backends import get_validator
except ImportError as e:
    print(f"Error importing VaultMind Forge modules: {e}", file=sys.stderr)
    print("Make sure vaultmind_forge is installed or in PYTHONPATH", file=sys.stderr)
    sys.exit(1)


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate images with SDXL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic generation
  python generate_sdxl.py --prompt "futuristic cityscape at sunset" --width 1024 --height 1024

  # High quality with more steps
  python generate_sdxl.py --prompt "portrait of a cyberpunk character" --steps 50 --batch 4

  # With custom output directory
  python generate_sdxl.py --prompt "fantasy landscape" --output ./my_outputs
        '''
    )

    parser.add_argument(
        '--prompt',
        type=str,
        required=True,
        help='Text prompt for image generation'
    )

    parser.add_argument(
        '--negative-prompt',
        type=str,
        default='low quality, blurry, distorted, bad anatomy, watermark',
        help='Negative prompt (things to avoid)'
    )

    parser.add_argument(
        '--width',
        type=int,
        default=1024,
        help='Image width (must be multiple of 64, default: 1024)'
    )

    parser.add_argument(
        '--height',
        type=int,
        default=1024,
        help='Image height (must be multiple of 64, default: 1024)'
    )

    parser.add_argument(
        '--steps',
        type=int,
        default=30,
        help='Number of diffusion steps (20-100, default: 30)'
    )

    parser.add_argument(
        '--guidance-scale',
        type=float,
        default=7.5,
        help='Classifier-free guidance scale (1.0-20.0, default: 7.5)'
    )

    parser.add_argument(
        '--batch',
        type=int,
        default=1,
        help='Batch size (number of images to generate, default: 1)'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility (default: random)'
    )

    parser.add_argument(
        '--backend',
        type=str,
        default='placeholder',
        choices=['placeholder', 'sdxl_base', 'sdxl_turbo'],
        help='Generation backend (default: placeholder)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='Output directory (default: output)'
    )

    parser.add_argument(
        '--use-refiner',
        action='store_true',
        help='Use SDXL refiner for enhanced quality'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Run quality validation on generated images'
    )

    parser.add_argument(
        '--track-lineage',
        action='store_true',
        help='Save lineage tracking record'
    )

    parser.add_argument(
        '--json-output',
        action='store_true',
        help='Output results as JSON'
    )

    return parser.parse_args()


def validate_dimensions(width, height):
    """Validate that dimensions are multiples of 64"""
    if width % 64 != 0:
        raise ValueError(f"Width must be multiple of 64, got {width}")
    if height % 64 != 0:
        raise ValueError(f"Height must be multiple of 64, got {height}")


def print_progress(message, prefix="[INFO]"):
    """Print progress message"""
    print(f"{prefix} {message}", file=sys.stderr)


def main():
    """Main execution"""
    args = parse_args()

    try:
        # Validate dimensions
        validate_dimensions(args.width, args.height)

        # Create output directory
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        print_progress(f"Output directory: {output_dir.absolute()}")

        # Create generation config
        config = GenerationConfig(
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            width=args.width,
            height=args.height,
            steps=args.steps,
            guidance_scale=args.guidance_scale,
            seed=args.seed,
            batch_size=args.batch,
            use_refiner=args.use_refiner
        )

        print_progress("Generation Configuration:")
        print_progress(f"  Prompt: {config.prompt[:60]}...")
        print_progress(f"  Size: {config.width}x{config.height}")
        print_progress(f"  Steps: {config.steps}")
        print_progress(f"  Guidance: {config.guidance_scale}")
        print_progress(f"  Batch: {config.batch_size}")
        print_progress(f"  Backend: {args.backend}")
        if config.seed:
            print_progress(f"  Seed: {config.seed}")

        # Initialize generator
        print_progress("Initializing generator...")

        # Create generator with specified backend
        backend_map = {
            'placeholder': GenerationBackend.PLACEHOLDER,
            'sdxl_base': GenerationBackend.SDXL_BASE,
            'sdxl_turbo': GenerationBackend.SDXL_TURBO
        }

        backend = backend_map.get(args.backend, GenerationBackend.PLACEHOLDER)

        generator = DiffusionGenerator(backend=backend)

        # Load models
        if backend != GenerationBackend.PLACEHOLDER:
            print_progress(f"Loading {args.backend} models...")
            print_progress("  This may take a few minutes on first run (downloading ~7GB)")
            generator.load_models(
                enable_xformers=True,
                enable_attention_slicing=True
            )
        else:
            print_progress("[WARN] Using placeholder backend (test mode)")
            print_progress("  Use --backend sdxl_turbo or sdxl_base for real generation")
            generator.load_models()  # Call load_models for placeholder too

        # Generate
        print_progress("Generating...")
        result = generator.generate(config)

        # Save images
        generated_files = []
        for i, img in enumerate(result.images):
            filename = f"generated_{i+1:03d}.png"
            filepath = output_dir / filename
            img.save(filepath)
            generated_files.append(str(filepath))
            print_progress(f"  Generated: {filename}")

        # Validation
        if args.validate:
            print_progress("Running quality validation...")
            try:
                validator = get_validator('basic')
                for filepath in generated_files:
                    result = validator.validate(filepath)
                    print_progress(f"  {Path(filepath).name}: score={result.get('score', 'N/A')}")
            except Exception as e:
                print_progress(f"[WARN] Validation failed: {e}", prefix="[WARN]")

        # Lineage tracking
        if args.track_lineage:
            print_progress("Saving lineage record...")
            try:
                tracker = LineageTracker()
                # TODO: Create proper lineage record
                print_progress("  Lineage tracking not yet fully implemented")
            except Exception as e:
                print_progress(f"[WARN] Lineage tracking failed: {e}", prefix="[WARN]")

        # Output results
        print_progress("[OK] Generation complete!")
        print_progress(f"  Generated {len(generated_files)} image(s)")
        print_progress(f"  Location: {output_dir.absolute()}")

        # JSON output
        if args.json_output:
            result = {
                'success': True,
                'config': {
                    'prompt': args.prompt,
                    'width': args.width,
                    'height': args.height,
                    'steps': args.steps,
                    'batch': args.batch,
                    'backend': args.backend
                },
                'outputs': generated_files,
                'output_dir': str(output_dir.absolute())
            }
            print(json.dumps(result, indent=2))
        else:
            # Simple text output for CLI
            for filepath in generated_files:
                print(filepath)

        return 0

    except Exception as e:
        print(f"[ERROR] Generation failed: {e}", file=sys.stderr)

        if args.json_output:
            error_result = {
                'success': False,
                'error': str(e)
            }
            print(json.dumps(error_result, indent=2))

        return 1


if __name__ == '__main__':
    sys.exit(main())
