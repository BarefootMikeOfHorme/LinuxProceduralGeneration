#!/usr/bin/env python3
"""
Validator Comparison Tool

Compares heuristic vs advanced validation metrics to demonstrate differences
and help calibrate thresholds for production use.

Usage:
    python scripts/compare_validators.py <image_path>
    python scripts/compare_validators.py <image_path> --reference <ref_path>
"""

import sys
from pathlib import Path
from typing import Optional
import time

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "vaultmind_forge"))

from vaultmind_forge.forge_validator import metrics
from vaultmind_forge.forge_validator import metrics_advanced


def compare_anatomy(asset_path: Path):
    """Compare anatomy scoring implementations"""
    print("\n" + "="*70)
    print("ANATOMY SCORING COMPARISON")
    print("="*70)

    # Heuristic
    start = time.perf_counter()
    score_heuristic = metrics.anatomy_score(asset_path)
    time_heuristic = (time.perf_counter() - start) * 1000

    # Advanced
    start = time.perf_counter()
    score_advanced, detailed = metrics_advanced.anatomy_score_advanced(asset_path)
    time_advanced = (time.perf_counter() - start) * 1000

    print(f"\n{'Metric':<30} {'Heuristic':<15} {'Advanced':<15}")
    print("-" * 60)
    print(f"{'Overall Score':<30} {score_heuristic:<15.4f} {score_advanced:<15.4f}")
    print(f"{'Execution Time (ms)':<30} {time_heuristic:<15.2f} {time_advanced:<15.2f}")

    print(f"\nAdvanced Breakdown:")
    print(f"  Golden Ratio Score:        {detailed.golden_ratio_score:.4f}")
    print(f"  Symmetry Score:            {detailed.symmetry_score:.4f}")
    print(f"  Proportion Score:          {detailed.proportion_score:.4f}")
    print(f"  Edge Quality Score:        {detailed.edge_quality_score:.4f}")
    print(f"  Pose Plausibility Score:   {detailed.pose_plausibility_score:.4f}")
    print(f"  Landmark Score:            {detailed.landmark_score:.4f}")

    print(f"\nDifference: {abs(score_advanced - score_heuristic):.4f} "
          f"({abs(score_advanced - score_heuristic) / max(score_heuristic, 0.01) * 100:.1f}%)")


def compare_prompt_alignment(asset_path: Path):
    """Compare prompt alignment implementations"""
    print("\n" + "="*70)
    print("PROMPT ALIGNMENT COMPARISON")
    print("="*70)

    # Heuristic
    start = time.perf_counter()
    score_heuristic = metrics.prompt_alignment_score(asset_path, None)
    time_heuristic = (time.perf_counter() - start) * 1000

    # Advanced
    start = time.perf_counter()
    score_advanced, detailed = metrics_advanced.prompt_alignment_score_advanced(asset_path, None)
    time_advanced = (time.perf_counter() - start) * 1000

    print(f"\n{'Metric':<30} {'Heuristic':<15} {'Advanced':<15}")
    print("-" * 60)
    print(f"{'Overall Score':<30} {score_heuristic:<15.4f} {score_advanced:<15.4f}")
    print(f"{'Execution Time (ms)':<30} {time_heuristic:<15.2f} {time_advanced:<15.2f}")

    print(f"\nAdvanced Breakdown:")
    print(f"  Color Harmony Score:       {detailed.color_harmony_score:.4f}")
    print(f"  Composition Score:         {detailed.composition_score:.4f}")
    print(f"  Detail Richness Score:     {detailed.detail_richness_score:.4f}")
    print(f"  Aesthetic Score:           {detailed.aesthetic_score:.4f}")
    print(f"  Perceptual Quality Score:  {detailed.perceptual_quality_score:.4f}")

    print(f"\nDifference: {abs(score_advanced - score_heuristic):.4f} "
          f"({abs(score_advanced - score_heuristic) / max(score_heuristic, 0.01) * 100:.1f}%)")


def compare_consistency(asset_path: Path, reference_path: Optional[Path] = None):
    """Compare consistency scoring implementations"""
    print("\n" + "="*70)
    print("CONSISTENCY SCORING COMPARISON")
    print("="*70)

    if reference_path:
        print(f"Reference: {reference_path.name}")
    else:
        print("Mode: Self-consistency")

    # Heuristic
    start = time.perf_counter()
    score_heuristic = metrics.consistency_score(asset_path, reference_path)
    time_heuristic = (time.perf_counter() - start) * 1000

    # Advanced
    start = time.perf_counter()
    score_advanced, detailed = metrics_advanced.consistency_score_advanced(asset_path, reference_path)
    time_advanced = (time.perf_counter() - start) * 1000

    print(f"\n{'Metric':<30} {'Heuristic':<15} {'Advanced':<15}")
    print("-" * 60)
    print(f"{'Overall Score':<30} {score_heuristic:<15.4f} {score_advanced:<15.4f}")
    print(f"{'Execution Time (ms)':<30} {time_heuristic:<15.2f} {time_advanced:<15.2f}")

    print(f"\nAdvanced Breakdown:")
    print(f"  SSIM Score:                {detailed.ssim_score:.4f}")
    print(f"  Color Consistency Score:   {detailed.color_consistency_score:.4f}")
    print(f"  Structural Consistency:    {detailed.structural_consistency_score:.4f}")
    print(f"  Perceptual Hash Score:     {detailed.perceptual_hash_score:.4f}")
    print(f"  Style Consistency Score:   {detailed.style_consistency_score:.4f}")

    print(f"\nDifference: {abs(score_advanced - score_heuristic):.4f} "
          f"({abs(score_advanced - score_heuristic) / max(score_heuristic, 0.01) * 100:.1f}%)")


def main():
    """Main comparison function"""
    import argparse

    parser = argparse.ArgumentParser(description="Compare validation metric implementations")
    parser.add_argument("image", type=Path, help="Path to image asset")
    parser.add_argument("--reference", "-r", type=Path, help="Optional reference image for consistency")
    parser.add_argument("--metric", "-m", choices=["anatomy", "prompt", "consistency", "all"],
                       default="all", help="Which metric to compare")

    args = parser.parse_args()

    if not args.image.exists():
        print(f"Error: Image not found: {args.image}")
        return 1

    if args.reference and not args.reference.exists():
        print(f"Error: Reference image not found: {args.reference}")
        return 1

    print("="*70)
    print("VAULTMIND FORGE - VALIDATOR COMPARISON")
    print("="*70)
    print(f"Asset: {args.image}")
    print(f"Resolution: {_get_image_size(args.image)}")

    try:
        if args.metric in ("anatomy", "all"):
            compare_anatomy(args.image)

        if args.metric in ("prompt", "all"):
            compare_prompt_alignment(args.image)

        if args.metric in ("consistency", "all"):
            compare_consistency(args.image, args.reference)

        print("\n" + "="*70)
        print("COMPARISON COMPLETE")
        print("="*70)
        print("\nInterpretation:")
        print("  - Advanced metrics provide more detailed analysis")
        print("  - Scores may differ due to additional factors considered")
        print("  - Execution time reflects algorithmic complexity")
        print("  - For production, use advanced metrics for higher fidelity")

    except Exception as e:
        print(f"\nError during comparison: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


def _get_image_size(path: Path) -> str:
    """Get image dimensions"""
    from PIL import Image
    with Image.open(path) as img:
        return f"{img.width}x{img.height}"


if __name__ == "__main__":
    sys.exit(main())
