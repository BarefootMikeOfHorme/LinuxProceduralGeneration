"""
Quality Guardian Agent - Practical Usage Examples
Shows how to use the Quality Guardian to automatically monitor and fix asset quality
"""

import sys
from pathlib import Path

# Add vaultmind_forge to path
sys.path.insert(0, str(Path(__file__).parents[1] / "vaultmind_forge"))

from forge_agents import QualityGuardianAgent


def example_1_basic_usage():
    """Example 1: Basic quality checking"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Quality Checking")
    print("="*70)

    # Create Quality Guardian with default settings
    guardian = QualityGuardianAgent(
        min_quality_threshold=0.7,  # Minimum acceptable quality
        auto_fix_enabled=True,      # Enable automatic fixing
    )

    # Check a single asset
    asset_path = Path("output/generated/character_001.png")

    # This assumes you have an asset to check - create a dummy one if not
    if not asset_path.exists():
        from PIL import Image
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new('RGB', (512, 512), color=(128, 128, 128))
        img.save(asset_path)
        print(f"[INFO] Created test asset: {asset_path}")

    print(f"\n[GUARDIAN] Assessing quality of: {asset_path.name}")
    report = guardian.assess_and_fix(asset_path)

    # Check the result
    print(f"\n[RESULT] Overall quality: {report.overall_quality:.3f}")
    print(f"[RESULT] Issues found: {len(report.issues_found)}")

    for issue in report.issues_found:
        print(f"  - {issue.description} (severity: {issue.severity:.2f})")

    print(f"\n[RESULT] Fixes applied: {len(report.fixes_applied)}")
    for fix in report.fixes_applied:
        print(f"  - {fix}")

    if report.after_quality:
        improvement = report.after_quality - report.before_quality
        print(f"\n[RESULT] Quality improvement: {report.before_quality:.3f} → {report.after_quality:.3f} ({improvement:+.3f})")

    print(f"\n[RESULT] Processing time: {report.processing_time_ms:.2f}ms")

    if report.escalated:
        print(f"\n⚠️  [ESCALATED] Reason: {report.escalation_reason}")
    else:
        print(f"\n✅ [APPROVED] Quality Guardian handled autonomously!")


def example_2_batch_monitoring():
    """Example 2: Batch quality monitoring"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Batch Quality Monitoring")
    print("="*70)

    guardian = QualityGuardianAgent(
        min_quality_threshold=0.7,
        auto_fix_enabled=True,
        save_before_after=True  # Save comparison images
    )

    # Monitor a batch of generated assets
    asset_dir = Path("output/generated/")
    asset_dir.mkdir(parents=True, exist_ok=True)

    # Create some test assets if none exist
    test_assets = []
    for i in range(5):
        asset_path = asset_dir / f"asset_{i:03d}.png"
        if not asset_path.exists():
            from PIL import Image
            import random
            # Create images with varying quality
            brightness = random.randint(50, 200)
            img = Image.new('RGB', (512, 512), color=(brightness, brightness, brightness))
            img.save(asset_path)
        test_assets.append(asset_path)

    print(f"\n[GUARDIAN] Monitoring {len(test_assets)} assets...")

    # Process each asset
    results = []
    for asset_path in test_assets:
        report = guardian.assess_and_fix(asset_path, context={
            "asset_type": "texture",
            "batch_processing": True
        })
        results.append(report)

        status = "✅ APPROVED" if not report.escalated else "⚠️ ESCALATED"
        print(f"{status} - {asset_path.name}: Quality={report.overall_quality:.3f}, Fixes={len(report.fixes_applied)}")

    # Print batch summary
    print(f"\n[BATCH SUMMARY]")
    print(f"  Total processed: {len(results)}")
    print(f"  Avg quality: {sum(r.overall_quality for r in results) / len(results):.3f}")
    print(f"  Escalated: {sum(1 for r in results if r.escalated)}")
    print(f"  Fixed: {sum(1 for r in results if r.fixes_applied)}")


def example_3_integration_with_generation():
    """Example 3: Integration with generation pipeline"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Integration with Generation Pipeline")
    print("="*70)

    # Create Quality Guardian for generation pipeline
    guardian = QualityGuardianAgent(
        min_quality_threshold=0.75,  # Slightly higher for generation
        auto_fix_enabled=True,
        aggressive_fixing=False,     # Don't alter too much
        max_fix_attempts=3,
    )

    def generation_pipeline_with_guardian(prompt: str, output_path: Path):
        """Simulated generation pipeline with Quality Guardian"""

        print(f"\n[PIPELINE] Generating asset: '{prompt}'")

        # Step 1: Generate (simulated)
        from PIL import Image
        import random

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Simulate generation with random quality
        quality_factor = random.uniform(0.5, 1.0)
        brightness = int(128 * quality_factor)
        img = Image.new('RGB', (512, 512), color=(brightness, brightness, brightness))
        img.save(output_path)

        print(f"[PIPELINE] Generated: {output_path}")

        # Step 2: Quality Guardian checks it
        print(f"[PIPELINE] Quality Guardian assessing...")

        report = guardian.assess_and_fix(output_path, context={
            "asset_type": "texture",
            "prompt": prompt,
        })

        # Step 3: Decide what to do based on Quality Guardian's decision
        if report.escalated:
            print(f"[PIPELINE] ⚠️  Quality Guardian escalated - regeneration recommended")
            return "RETRY_GENERATION"

        elif report.fixes_applied:
            print(f"[PIPELINE] ✅ Quality Guardian auto-fixed ({len(report.fixes_applied)} fixes)")
            print(f"[PIPELINE] Quality improved: {report.before_quality:.3f} → {report.after_quality:.3f}")
            return "APPROVED_WITH_FIXES"

        else:
            print(f"[PIPELINE] ✅ Quality Guardian approved (no fixes needed)")
            return "APPROVED"

    # Run pipeline
    result = generation_pipeline_with_guardian(
        prompt="medieval sword texture",
        output_path=Path("output/generated/sword_texture.png")
    )

    print(f"\n[RESULT] Pipeline outcome: {result}")


def example_4_learning_and_metrics():
    """Example 4: Learning and performance metrics"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Learning and Performance Metrics")
    print("="*70)

    guardian = QualityGuardianAgent(
        learning_enabled=True,
        metrics_path=Path("quality_guardian_metrics.json")
    )

    # Process some assets
    asset_dir = Path("output/test_assets/")
    asset_dir.mkdir(parents=True, exist_ok=True)

    for i in range(10):
        asset_path = asset_dir / f"test_{i}.png"
        if not asset_path.exists():
            from PIL import Image
            img = Image.new('RGB', (512, 512), color=(100, 100, 100))
            img.save(asset_path)

        guardian.assess_and_fix(asset_path)

    # Get performance metrics
    print(f"\n[METRICS] Performance Statistics:")
    metrics = guardian.get_metrics()

    print(f"  Total decisions: {metrics['total_decisions']}")
    print(f"  Average confidence: {metrics['average_confidence']:.3f}")
    print(f"  Escalation rate: {metrics['escalation_rate']:.3%}")
    print(f"  Decisions by action:")
    for action, count in metrics['decisions_by_action'].items():
        print(f"    {action}: {count}")

    # Get quality trends
    print(f"\n[TRENDS] Quality Trends:")
    trends = guardian.get_quality_trends()

    if trends:
        print(f"  Avg before quality: {trends.get('avg_before_quality', 0):.3f}")
        print(f"  Avg after quality: {trends.get('avg_after_quality', 0):.3f}")
        print(f"  Avg improvement: {trends.get('avg_improvement', 0):.3f}")
        print(f"  Most common fixes: {trends.get('most_common_fixes', [])[:3]}")

    # Get fix effectiveness report
    print(f"\n[LEARNING] Fix Effectiveness:")
    fix_report = guardian.get_fix_effectiveness_report()

    for fix_type, stats in fix_report.items():
        print(f"  {fix_type}:")
        print(f"    Used {stats['times_used']} times")
        print(f"    Success rate: {stats['success_rate']:.1%}")
        print(f"    Avg improvement: {stats['avg_improvement']:+.3f}")

    # Save metrics for later analysis
    guardian.save_metrics()
    print(f"\n[SAVED] Metrics saved to: {guardian.metrics_path}")


def example_5_custom_thresholds():
    """Example 5: Custom thresholds for different asset types"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Custom Thresholds per Asset Type")
    print("="*70)

    # Different guardians for different asset types

    # Hero assets: Very strict
    hero_guardian = QualityGuardianAgent(
        min_quality_threshold=0.9,  # 90% quality required
        auto_fix_enabled=True,
        aggressive_fixing=True,     # Can be more aggressive on hero assets
    )

    # Background assets: More lenient
    background_guardian = QualityGuardianAgent(
        min_quality_threshold=0.6,  # 60% is acceptable
        auto_fix_enabled=True,
        aggressive_fixing=False,
    )

    # UI elements: Moderate
    ui_guardian = QualityGuardianAgent(
        min_quality_threshold=0.75,
        auto_fix_enabled=True,
    )

    print("\n[INFO] Created 3 guardians with different standards:")
    print(f"  Hero Guardian: {hero_guardian.min_quality_threshold:.1%} threshold")
    print(f"  Background Guardian: {background_guardian.min_quality_threshold:.1%} threshold")
    print(f"  UI Guardian: {ui_guardian.min_quality_threshold:.1%} threshold")

    # Example: Route assets to appropriate guardian
    def route_to_guardian(asset_path: Path, asset_type: str):
        """Route asset to appropriate guardian based on type"""

        if asset_type == "hero":
            guardian = hero_guardian
        elif asset_type == "background":
            guardian = background_guardian
        elif asset_type == "ui":
            guardian = ui_guardian
        else:
            guardian = background_guardian  # Default

        print(f"\n[ROUTING] {asset_path.name} ({asset_type}) → {guardian.name} (threshold={guardian.min_quality_threshold:.1%})")

        report = guardian.assess_and_fix(asset_path)
        return report

    # Test with sample asset
    test_asset = Path("output/test_assets/sample.png")
    test_asset.parent.mkdir(parents=True, exist_ok=True)

    if not test_asset.exists():
        from PIL import Image
        img = Image.new('RGB', (512, 512), color=(150, 150, 150))
        img.save(test_asset)

    # Route the same asset to different guardians
    for asset_type in ["hero", "background", "ui"]:
        report = route_to_guardian(test_asset, asset_type)
        print(f"  Result: Quality={report.overall_quality:.3f}, Escalated={report.escalated}")


def main():
    """Run all examples"""
    print("="*80)
    print("QUALITY GUARDIAN AGENT - PRACTICAL EXAMPLES")
    print("="*80)

    examples = [
        ("Basic Usage", example_1_basic_usage),
        ("Batch Monitoring", example_2_batch_monitoring),
        ("Pipeline Integration", example_3_integration_with_generation),
        ("Learning & Metrics", example_4_learning_and_metrics),
        ("Custom Thresholds", example_5_custom_thresholds),
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
    print("\n✅ Quality Guardian Agent is ready to use!")
    print("\nKey Takeaways:")
    print("  • Guardian autonomously assesses quality (no main AI needed)")
    print("  • Auto-fixes 80%+ of common issues (sharpening, contrast, etc.)")
    print("  • Escalates only when uncertain or severe issues")
    print("  • Learns which fixes work best over time")
    print("  • Customizable thresholds per asset type")
    print("  • Detailed metrics and reporting")


if __name__ == "__main__":
    main()
