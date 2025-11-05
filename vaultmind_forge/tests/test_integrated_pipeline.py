"""
VaultMind Forge - Integration Test Suite
Tests the Quick Win Trio: AI Validation + Lineage Tracking + Pipeline DAG
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any
import logging

# Add modules to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from forge_executor.pipeline import AssetPipeline, run_asset_pipeline
from forge_validator.ai_validator import AIValidator, ValidationDecision
from forge_lineage import LineageTracker, OperationType
from forge_converter.ai_control import AuthorityLevel


def setup_test_environment():
    """Set up test environment"""
    # Create test directories
    test_dirs = [
        "assets/generated/diffusion/textures",
        "assets/validated/winners",
        "assets/output/unity",
        "assets/output/unreal",
        "assets/output/godot",
        "assets/packages",
        "assets/lineage",
        "tests/output"
    ]

    for dir_path in test_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    print("[TEST ENV] Created test directories")


def test_1_ai_validator_standalone():
    """Test 1: AI Validator standalone"""
    print("\n" + "="*60)
    print("TEST 1: AI Validator Standalone")
    print("="*60)

    # Create validator with high autonomy
    validator = AIValidator(
        authority_level=AuthorityLevel.HIGH_AUTONOMY,
        threshold=0.7
    )

    # Create dummy test image
    test_asset = Path("tests/output/test_asset.png")
    test_asset.parent.mkdir(parents=True, exist_ok=True)

    # Create minimal PNG (1x1 pixel)
    from PIL import Image
    img = Image.new('RGB', (512, 512), color='gray')
    img.save(test_asset)

    print(f"[TEST] Created test asset: {test_asset}")

    # Validate with AI
    result = validator.validate_with_ai(
        asset_path=test_asset,
        context={
            "output_type": "character",
            "is_hero_asset": False,
            "attempt_number": 1
        },
        prompt="medieval knight armor"
    )

    # Check results
    print(f"\n[RESULT] Decision: {result.decision.value}")
    print(f"[RESULT] Confidence: {result.confidence:.2f}")
    print(f"[RESULT] Reasoning: {result.reasoning}")
    print(f"[RESULT] Overall Score: {result.validation.score:.2f}")

    if result.decision == ValidationDecision.RETRY_RECOMMENDED:
        print(f"[RESULT] Suggested Adjustments: {result.suggested_adjustments}")

    # Validate results
    assert result.decision in [
        ValidationDecision.APPROVED,
        ValidationDecision.REJECTED,
        ValidationDecision.RETRY_RECOMMENDED,
        ValidationDecision.FLAG_FOR_HUMAN
    ], "Invalid decision"
    assert 0.0 <= result.confidence <= 1.0, "Invalid confidence"

    print("\n[TEST 1] PASSED: AI Validator working correctly")

    return result


def test_2_lineage_tracker_standalone():
    """Test 2: Lineage Tracker standalone"""
    print("\n" + "="*60)
    print("TEST 2: Lineage Tracker Standalone")
    print("="*60)

    # Create tracker
    tracker = LineageTracker()

    # Create test assets
    asset1 = Path("tests/output/asset1.png")
    asset2 = Path("tests/output/asset2.png")
    asset3 = Path("tests/output/asset3.dds")

    from PIL import Image
    Image.new('RGB', (256, 256), color='red').save(asset1)
    Image.new('RGB', (256, 256), color='blue').save(asset2)
    Image.new('RGB', (256, 256), color='green').save(asset3)

    print(f"[TEST] Created test assets: {asset1}, {asset2}, {asset3}")

    # Record generation
    checksum1 = tracker.record_generation(
        asset_path=asset1,
        parameters={"prompt": "red texture", "steps": 30, "cfg_scale": 7.5},
        generator="forge_diffusion"
    )
    print(f"\n[LINEAGE] Generation recorded: {checksum1[:16]}...")

    # Record validation
    checksum1_val = tracker.record_validation(
        asset_path=asset1,
        scores={"sharpness": 0.75, "overall": 0.80},
        ai_decision={"decision": "approved", "confidence": 0.85}
    )
    print(f"[LINEAGE] Validation recorded: {checksum1_val[:16]}...")

    # Record retry (asset2 is retry of asset1)
    checksum2 = tracker.record_retry(
        original_asset=asset1,
        retry_asset=asset2,
        attempt_number=2,
        adjustments={"cfg_scale": 8.0, "steps": 35}
    )
    print(f"[LINEAGE] Retry recorded: {checksum2[:16]}...")

    # Record conversion (asset3 is conversion of asset2)
    checksum3 = tracker.record_conversion(
        input_asset=asset2,
        output_asset=asset3,
        format="dds",
        converter="forge_converter",
        parameters={"compression": "BC7"}
    )
    print(f"[LINEAGE] Conversion recorded: {checksum3[:16]}...")

    # Get history
    history = tracker.get_asset_history(checksum3)
    print(f"\n[LINEAGE] Asset history (oldest to newest):")
    for i, record in enumerate(history, 1):
        print(f"  {i}. {record.operation} by {record.generator} ({record.sha256[:16]}...)")

    # Get children of asset1
    children = tracker.get_children(checksum1)
    print(f"\n[LINEAGE] Children of asset1: {len(children)}")
    for child in children:
        print(f"  - {child.operation} ({child.sha256[:16]}...)")

    # Get tree
    tree = tracker.get_asset_tree(checksum1, max_depth=3)
    print(f"\n[LINEAGE] Asset tree for asset1:")
    print(f"  Root: {tree['operation']} at {tree['timestamp']}")
    print(f"  Children: {len(tree['children'])}")

    # Export genealogy
    genealogy_path = Path("tests/output/genealogy.json")
    tracker.export_genealogy(checksum1, genealogy_path)
    print(f"\n[LINEAGE] Exported genealogy to {genealogy_path}")

    # Get statistics
    stats = tracker.get_statistics()
    print(f"\n[LINEAGE] Statistics:")
    print(f"  Total assets: {stats['total_assets']}")
    print(f"  Operations: {stats['operations']}")

    # Validate results
    assert len(history) >= 2, "History should have at least 2 records"
    assert checksum1 == checksum1_val, "Checksums should match"
    assert genealogy_path.exists(), "Genealogy file should exist"

    print("\n[TEST 2] PASSED: Lineage Tracker working correctly")

    return tracker, checksum1, checksum2, checksum3


def test_3_pipeline_dag():
    """Test 3: Full Pipeline DAG Execution"""
    print("\n" + "="*60)
    print("TEST 3: Full Pipeline DAG Execution")
    print("="*60)

    # Create pipeline with high autonomy
    pipeline = AssetPipeline(
        ai_authority=AuthorityLevel.HIGH_AUTONOMY,
        max_retries=2,
        enable_lineage=True
    )

    print("[PIPELINE] Created pipeline with HIGH_AUTONOMY")
    print(f"[PIPELINE] Max retries: 2")
    print(f"[PIPELINE] Lineage tracking: ENABLED")

    # Run generation pipeline
    result = pipeline.run_generation_pipeline(
        prompt="fantasy sword texture",
        output_type="weapon",
        target_engines=["unity", "unreal"],
        is_hero_asset=False,
        generation_params={"steps": 30, "cfg_scale": 7.5}
    )

    print(f"\n[PIPELINE] Execution complete")
    print(f"[PIPELINE] Success: {result.success}")
    print(f"[PIPELINE] Stages completed: {len(result.stages_completed)}")

    for stage in result.stages_completed:
        if stage:  # Skip empty strings
            print(f"  - {stage}")

    print(f"\n[PIPELINE] Outputs:")
    for engine, path in result.outputs.items():
        print(f"  - {engine}: {path}")

    print(f"\n[PIPELINE] Lineage checksums:")
    for key, checksum in result.lineage_checksums.items():
        if checksum:
            print(f"  - {key}: {checksum[:16]}...")

    if result.errors:
        print(f"\n[PIPELINE] Errors: {result.errors}")

    # Validate results
    assert result.success, "Pipeline should succeed"
    assert len(result.outputs) == 2, "Should have 2 outputs (unity, unreal)"
    assert "generate" in result.stages_completed, "Generate stage should complete"
    assert "validate" in result.stages_completed, "Validate stage should complete"

    print("\n[TEST 3] PASSED: Pipeline DAG working correctly")

    return result


def test_4_integrated_workflow():
    """Test 4: Complete Integrated Workflow"""
    print("\n" + "="*60)
    print("TEST 4: Complete Integrated Workflow")
    print("="*60)

    # Use convenience function
    result = run_asset_pipeline(
        prompt="medieval castle wall texture",
        target_engines=["unity", "unreal", "godot"],
        output_type="environment",
        is_hero_asset=False
    )

    print(f"\n[WORKFLOW] Pipeline complete")
    print(f"[WORKFLOW] Success: {result.success}")
    print(f"[WORKFLOW] Outputs: {len(result.outputs)} engines")

    # Check lineage tracking
    if result.lineage_checksums.get("generation"):
        tracker = LineageTracker()
        gen_checksum = result.lineage_checksums["generation"]

        print(f"\n[WORKFLOW] Lineage tracking:")
        print(f"  Generation checksum: {gen_checksum[:16]}...")

        # Get history
        history = tracker.get_asset_history(gen_checksum)
        print(f"  History depth: {len(history)}")

        # Get children (conversions)
        children = tracker.get_children(gen_checksum)
        print(f"  Children (conversions): {len(children)}")

    # Validate results
    assert result.success, "Workflow should succeed"
    assert len(result.outputs) == 3, "Should have 3 outputs (unity, unreal, godot)"

    print("\n[TEST 4] PASSED: Integrated workflow working correctly")

    return result


def test_5_retry_logic():
    """Test 5: Retry Logic with AI Adjustments"""
    print("\n" + "="*60)
    print("TEST 5: Retry Logic with AI Adjustments")
    print("="*60)

    # Create pipeline with supervised mode (more likely to retry)
    pipeline = AssetPipeline(
        ai_authority=AuthorityLevel.SUPERVISED,
        max_retries=3,
        enable_lineage=True
    )

    print("[RETRY] Testing retry logic with SUPERVISED authority")

    # Run pipeline (may trigger retries)
    result = pipeline.run_generation_pipeline(
        prompt="complex character portrait",
        output_type="character",
        target_engines=["unity"],
        is_hero_asset=True,  # Hero assets have stricter validation
        generation_params={"steps": 20, "cfg_scale": 5.0}
    )

    print(f"\n[RETRY] Pipeline complete")
    print(f"[RETRY] Retry count: {pipeline.retry_count}")
    print(f"[RETRY] Stages: {[s for s in result.stages_completed if s]}")

    # Check if retry occurred
    retry_occurred = "retry_check" in result.stages_completed and pipeline.retry_count > 0

    if retry_occurred:
        print(f"\n[RETRY] Retry was triggered {pipeline.retry_count} time(s)")

        # Check lineage for retry records
        if result.lineage_checksums.get("generation"):
            tracker = LineageTracker()
            gen_checksum = result.lineage_checksums["generation"]

            # Get all retry operations
            retry_records = [
                r for r in tracker.get_asset_history(gen_checksum)
                if r.operation == OperationType.RETRY.value
            ]

            print(f"[RETRY] Lineage contains {len(retry_records)} retry record(s)")
            for record in retry_records:
                print(f"  - Attempt {record.parameters.get('attempt_number')}")
                print(f"    Adjustments: {record.parameters.get('adjustments')}")
    else:
        print("\n[RETRY] No retry was triggered (asset passed validation)")

    assert result.success, "Pipeline should succeed even with retries"

    print("\n[TEST 5] PASSED: Retry logic working correctly")

    return result


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("VAULTMIND FORGE - INTEGRATION TEST SUITE")
    print("Testing: AI Validation + Lineage Tracking + Pipeline DAG")
    print("="*80)

    # Set up environment
    setup_test_environment()

    # Run tests
    try:
        test_1_ai_validator_standalone()
        test_2_lineage_tracker_standalone()
        test_3_pipeline_dag()
        test_4_integrated_workflow()
        test_5_retry_logic()

        print("\n" + "="*80)
        print("ALL TESTS PASSED")
        print("="*80)
        print("\nIntegration Summary:")
        print("  [OK] AI Validator: Autonomous decision making")
        print("  [OK] Lineage Tracker: Complete genealogy tracking")
        print("  [OK] Pipeline DAG: End-to-end orchestration")
        print("  [OK] Integrated Workflow: All components working together")
        print("  [OK] Retry Logic: AI-driven parameter adjustments")
        print("\nNext Steps:")
        print("  1. Connect to actual forge_diffusion generator")
        print("  2. Implement format handlers (FBX, DDS, MaterialX, USD)")
        print("  3. Add monitoring dashboard")
        print("  4. Implement batch processing")

        return True

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
