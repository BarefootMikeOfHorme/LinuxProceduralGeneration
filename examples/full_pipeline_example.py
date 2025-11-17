#!/usr/bin/env python3
"""
VaultMind Forge - Full Pipeline Integration Example

Demonstrates all modules working together:
1. forge_monitor - Track resource usage
2. forge_agent - Plan and configure job
3. forge_validator - Validate outputs
4. forge_sr - Upscale assets
5. forge_semantic - Create resolution variants
6. forge_versioning - Version control assets
7. forge_video - Create video from frames

This is a complete end-to-end workflow showing how all modules integrate.
"""

from pathlib import Path
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "vaultmind_forge"))

from vaultmind_forge.forge_monitor import SystemMonitor, MetricsAggregator
from vaultmind_forge.forge_agent import (
    JobPlanner,
    OutputType,
    RenderStyle,
    QualityPreset,
)
from vaultmind_forge.forge_sr import SuperResolutionUpscaler, SRBackend
from vaultmind_forge.forge_semantic import SemanticDownrezzer, DownrezMode
from vaultmind_forge.forge_versioning import AssetVersionControl
from vaultmind_forge.forge_video import VideoGenerator, VideoConfig, VideoCodec


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def main():
    """Run full pipeline demonstration"""

    # Setup paths
    output_dir = Path("./output/full_pipeline_demo")
    output_dir.mkdir(parents=True, exist_ok=True)

    print_section("VaultMind Forge - Full Pipeline Demo")
    print("This demo shows all modules working together in a production workflow.\n")

    # ========================================================================
    # STEP 1: Initialize System Monitor
    # ========================================================================
    print_section("STEP 1: System Monitoring Setup")

    monitor = SystemMonitor(
        cpu_threshold=85.0,
        memory_threshold=90.0,
        gpu_temp_threshold=85.0,
    )

    print("[OK] System monitor initialized")
    snapshot = monitor.capture_snapshot()
    print(f"  CPU: {snapshot.cpu_percent:.1f}%")
    print(f"  Memory: {snapshot.memory_percent:.1f}% ({snapshot.memory_used_gb:.1f}GB / {snapshot.memory_total_gb:.1f}GB)")
    print(f"  Disk: {snapshot.disk_percent:.1f}%")
    if snapshot.gpu_count > 0:
        print(f"  GPU Count: {snapshot.gpu_count}")
        for i, temp in enumerate(snapshot.gpu_temperature):
            print(f"    GPU {i}: {snapshot.gpu_utilization[i]:.1f}% @ {temp:.1f}°C")

    # Start monitoring session
    monitor.start_session("full-pipeline-demo")

    # ========================================================================
    # STEP 2: Job Planning with forge_agent
    # ========================================================================
    print_section("STEP 2: Intelligent Job Planning")

    planner = JobPlanner()

    # Create a job using the planner
    job = planner.create_simple_job(
        name="Hero Character Design",
        prompt="heroic warrior with glowing sword, detailed armor, epic lighting",
        output_type=OutputType.CHARACTER_2D,
        render_style=RenderStyle.ANIME,
        quality=QualityPreset.HIGH,
        width=512,
        height=768,
        multi_pass=True,
        num_passes=3,
    )

    print(f"[OK] Job created: {job.name}")
    print(f"  ID: {job.id}")
    print(f"  Type: {job.output_type.value}")
    print(f"  Style: {job.render_style.value}")
    print(f"  Resolution: {job.aspect_ratio}")

    # Generate execution plan
    plan = planner.create_plan(job)

    print(f"\n[OK] Execution plan generated:")
    print(f"  Estimated time: {plan.estimated_time_minutes:.1f} minutes")
    print(f"  Estimated memory: {plan.estimated_memory_gb:.1f} GB")
    print(f"  Recommended helpers: {[h.value for h in plan.recommended_helpers]}")

    if plan.warnings:
        print(f"\n  [WARN]️  Warnings:")
        for warning in plan.warnings:
            print(f"    - {warning}")

    if plan.optimization_notes:
        print(f"\n  💡 Optimization notes:")
        for note in plan.optimization_notes:
            print(f"    - {note}")

    # Check if we have enough resources
    snapshot = monitor.capture_snapshot()
    if snapshot.memory_available_gb < plan.estimated_memory_gb:
        print(f"\n  [WARN]️  WARNING: Insufficient memory!")
        print(f"     Need {plan.estimated_memory_gb}GB, have {snapshot.memory_available_gb:.1f}GB available")
    else:
        print(f"\n  [OK] Sufficient resources available")

    # ========================================================================
    # STEP 3: Simulated Asset Generation (Placeholder)
    # ========================================================================
    print_section("STEP 3: Asset Generation (Simulated)")

    # In a real workflow, this would call forge_diffusion
    # For demo, we'll create placeholder files
    print("ℹ️  In production, this would generate assets using forge_diffusion")
    print("   For this demo, we'll simulate with placeholder images\n")

    # Create dummy asset files for demonstration
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np

    generated_assets = []
    for i in range(3):
        asset_path = output_dir / f"character_pass_{i+1}.png"

        # Create simple colored image as placeholder
        img = Image.new('RGB', (512, 768), color=(100 + i*50, 150 - i*30, 200 + i*20))
        draw = ImageDraw.Draw(img)

        # Add text
        text = f"Character Design\nPass {i+1}"
        draw.text((256, 384), text, fill=(255, 255, 255), anchor="mm")

        img.save(asset_path)
        generated_assets.append(asset_path)
        print(f"[OK] Generated asset {i+1}: {asset_path.name}")

    # Capture monitoring snapshot after generation
    monitor.capture_snapshot()

    # ========================================================================
    # STEP 4: Validation (Using existing validator)
    # ========================================================================
    print_section("STEP 4: Quality Validation")

    print("ℹ️  In production, this would use forge_validator with full metrics")
    print("   (sharpness, anatomy, prompt alignment, etc.)\n")

    # Simulate validation scores
    best_asset = generated_assets[1]  # Pick middle one as "winner"
    print(f"[OK] Best asset selected: {best_asset.name}")
    print(f"  Quality score: 0.87 (simulated)")

    # ========================================================================
    # STEP 5: Super Resolution Upscaling
    # ========================================================================
    print_section("STEP 5: Super Resolution Upscaling")

    upscaler = SuperResolutionUpscaler(enable_fallback=True)

    sr_output = output_dir / "character_upscaled_4x.png"

    print(f"Upscaling {best_asset.name} to 4x resolution...")
    sr_result = upscaler.upscale(
        input_path=best_asset,
        output_path=sr_output,
        scale_factor=4,
        backend=SRBackend.FALLBACK_LANCZOS,  # Using fallback for demo
    )

    print(f"\n[OK] Upscaled successfully:")
    print(f"  Original: {sr_result.original_size}")
    print(f"  Upscaled: {sr_result.upscaled_size}")
    print(f"  Scale: {sr_result.scale_factor}x")
    print(f"  Backend: {sr_result.backend_used.value}")
    print(f"  Processing time: {sr_result.processing_time_ms:.1f}ms")

    monitor.capture_snapshot()

    # ========================================================================
    # STEP 6: Semantic Downrezzing (Create variants)
    # ========================================================================
    print_section("STEP 6: Creating Resolution Variants")

    downrezzer = SemanticDownrezzer(preserve_edges=True)

    # Create downrez ladder
    sizes = [(1024, 1536), (512, 768), (256, 384)]

    print(f"Creating {len(sizes)} resolution variants...")
    downrez_results = downrezzer.create_downrez_ladder(
        input_path=sr_output,
        output_dir=output_dir / "variants",
        sizes=sizes,
    )

    print(f"\n[OK] Created {len(downrez_results)} variants:")
    for result in downrez_results:
        print(f"  - {result.downrezzed_size}: {result.output_path.name} ({result.processing_time_ms:.1f}ms)")

    monitor.capture_snapshot()

    # ========================================================================
    # STEP 7: Version Control
    # ========================================================================
    print_section("STEP 7: Asset Version Control")

    vcs = AssetVersionControl(repo_path=output_dir / "asset_repo")

    # Commit the final asset
    version = vcs.commit(
        asset_path=sr_output,
        message="Initial character design - Hero with glowing sword",
        metadata={
            "job_id": job.id,
            "quality_score": 0.87,
            "upscale_factor": 4,
            "style": job.render_style.value,
        }
    )

    print(f"[OK] Asset committed to version control:")
    print(f"  Version ID: {version.version_id}")
    print(f"  Checksum: {version.checksum[:16]}...")
    print(f"  Branch: main")

    # Create experimental branch
    exp_branch = vcs.create_branch(
        "alternative-style",
        "Exploring different visual styles"
    )

    print(f"\n[OK] Created branch: {exp_branch.name}")
    print(f"  Description: {exp_branch.description}")

    # Get version history
    history = vcs.get_history()
    print(f"\n[OK] Version history: {len(history)} commits")
    for ver in history:
        print(f"  - {ver.version_id}: {ver.message}")

    # ========================================================================
    # STEP 8: Video Generation (Slideshow)
    # ========================================================================
    print_section("STEP 8: Video Generation")

    video_gen = VideoGenerator()

    # Create slideshow from generated assets
    video_output = output_dir / "character_slideshow.mp4"

    print(f"Creating slideshow from {len(generated_assets)} frames...")

    try:
        video_result = video_gen.frames_to_video(
            frame_paths=generated_assets,
            output_path=video_output,
            config=VideoConfig(fps=2, codec=VideoCodec.H264),
            frame_duration=2.0,
        )

        print(f"\n[OK] Video created successfully:")
        print(f"  Output: {video_result.output_path.name}")
        print(f"  Duration: {video_result.duration_seconds:.1f}s")
        print(f"  Frames: {video_result.frame_count}")
        print(f"  Resolution: {video_result.resolution}")
        print(f"  Size: {video_result.file_size_mb:.2f} MB")
    except Exception as e:
        print(f"\n[WARN]️  Video generation skipped (FFmpeg not available)")
        print(f"   Error: {e}")

    # ========================================================================
    # STEP 9: Monitoring Summary
    # ========================================================================
    print_section("STEP 9: Resource Usage Summary")

    # Stop monitoring session and get summary
    summary = monitor.stop_session()

    print(f"Session: {summary['session_name']}")
    print(f"Duration: {summary['duration_seconds']:.1f} seconds")
    print(f"Snapshots: {summary['snapshot_count']}")

    print(f"\nCPU Usage:")
    print(f"  Average: {summary['cpu']['avg']:.1f}%")
    print(f"  Peak: {summary['cpu']['max']:.1f}%")

    print(f"\nMemory Usage:")
    print(f"  Average: {summary['memory']['avg']:.1f}%")
    print(f"  Peak: {summary['memory']['max']:.1f}%")

    print(f"\nProcess Stats:")
    print(f"  CPU (avg): {summary['process']['cpu_avg']:.1f}%")
    print(f"  Memory (peak): {summary['process']['memory_max_mb']:.1f} MB")

    if summary.get('gpu'):
        print(f"\nGPU Stats:")
        for i, util in enumerate(summary['gpu']['utilization_avg']):
            print(f"  GPU {i} utilization (avg): {util:.1f}%")

    if summary['alerts']:
        print(f"\n[WARN]️  Alerts during session: {len(summary['alerts'])}")
        for alert in summary['alerts'][:3]:  # Show first 3
            print(f"  - [{alert['level']}] {alert['message']}")

    # Generate performance report
    report = MetricsAggregator.generate_performance_report(monitor.snapshots)

    print(f"\nPerformance Analysis:")
    print(f"  CPU trend: {report['cpu']['trend']}")
    print(f"  Memory trend: {report['memory']['trend']}")
    print(f"  CPU anomalies detected: {report['cpu']['anomaly_count']}")

    # Export metrics
    metrics_file = output_dir / "session_metrics.json"
    monitor.export_metrics(metrics_file)
    print(f"\n[OK] Metrics exported to: {metrics_file}")

    # ========================================================================
    # Summary
    # ========================================================================
    print_section("Pipeline Complete!")

    print("[OK] All modules demonstrated successfully:\n")
    print("  1. [OK] forge_monitor - Tracked resource usage throughout pipeline")
    print("  2. [OK] forge_agent - Planned job with resource estimation")
    print("  3. [OK] Asset generation - Simulated (would use forge_diffusion)")
    print("  4. [OK] forge_validator - Quality validation (simulated)")
    print("  5. [OK] forge_sr - Upscaled asset to 4x resolution")
    print("  6. [OK] forge_semantic - Created resolution variants")
    print("  7. [OK] forge_versioning - Version control with branching")
    print("  8. [OK] forge_video - Created slideshow (if FFmpeg available)")
    print("  9. [OK] forge_monitor - Generated performance report")

    print(f"\n📁 Output directory: {output_dir.absolute()}")
    print(f"   - Generated assets: {len(generated_assets)} files")
    print(f"   - Upscaled asset: {sr_output.name}")
    print(f"   - Resolution variants: {len(downrez_results)} files")
    print(f"   - Version control repo: asset_repo/")
    print(f"   - Metrics: session_metrics.json")

    print("\n" + "="*60)
    print("  This is VaultMind Forge - Complete AI Asset Pipeline")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARN]️  Pipeline interrupted by user")
    except Exception as e:
        print(f"\n\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
