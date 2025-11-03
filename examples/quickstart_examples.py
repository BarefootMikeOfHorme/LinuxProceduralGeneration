#!/usr/bin/env python3
"""
VaultMind Forge - Quick Start Examples

Simple examples showing basic usage of each module.
Perfect for learning the API or quick reference.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "vaultmind_forge"))


def example_monitor():
    """forge_monitor - Basic system monitoring"""
    print("\n" + "="*60)
    print("Example 1: forge_monitor - System Monitoring")
    print("="*60 + "\n")

    from vaultmind_forge.forge_monitor import SystemMonitor

    # Create monitor
    monitor = SystemMonitor(cpu_threshold=85.0)

    # Capture snapshot
    snapshot = monitor.capture_snapshot()
    print(f"CPU: {snapshot.cpu_percent:.1f}%")
    print(f"Memory: {snapshot.memory_percent:.1f}%")
    print(f"Disk: {snapshot.disk_percent:.1f}%")

    # Track a session
    with monitor.track_session("my-task"):
        # Your code here
        import time
        time.sleep(0.1)

    summary = monitor.get_session_summary()
    print(f"\nSession duration: {summary['duration_seconds']:.2f}s")
    print(f"Avg CPU: {summary['cpu']['avg']:.1f}%")


def example_agent():
    """forge_agent - Job planning"""
    print("\n" + "="*60)
    print("Example 2: forge_agent - Job Planning")
    print("="*60 + "\n")

    from vaultmind_forge.forge_agent import (
        JobPlanner,
        OutputType,
        RenderStyle,
    )

    planner = JobPlanner()

    # Create simple job
    job = planner.create_simple_job(
        name="Hero Character",
        prompt="warrior with sword",
        output_type=OutputType.CHARACTER_2D,
        render_style=RenderStyle.ANIME,
    )

    print(f"Job created: {job.name}")
    print(f"  Type: {job.output_type.value}")
    print(f"  Style: {job.render_style.value}")

    # Generate execution plan
    plan = planner.create_plan(job)
    print(f"\nExecution plan:")
    print(f"  Estimated time: {plan.estimated_time_minutes:.1f} min")
    print(f"  Estimated memory: {plan.estimated_memory_gb:.1f} GB")
    print(f"  Helpers: {[h.value for h in plan.recommended_helpers]}")


def example_semantic():
    """forge_semantic - Image downscaling"""
    print("\n" + "="*60)
    print("Example 3: forge_semantic - Downscaling")
    print("="*60 + "\n")

    from vaultmind_forge.forge_semantic import SemanticDownrezzer, DownrezMode
    from PIL import Image

    # Create test image
    output_dir = Path("./output/quickstart")
    output_dir.mkdir(parents=True, exist_ok=True)

    test_img = output_dir / "test_highres.png"
    img = Image.new('RGB', (2048, 2048), color=(100, 150, 200))
    img.save(test_img)

    # Downrez image
    downrezzer = SemanticDownrezzer()
    result = downrezzer.downrez(
        input_path=test_img,
        output_path=output_dir / "test_lowres.png",
        target_size=(512, 512),
        mode=DownrezMode.QUALITY,
    )

    print(f"Downrezzed image:")
    print(f"  From: {result.original_size}")
    print(f"  To: {result.downrezzed_size}")
    print(f"  Time: {result.processing_time_ms:.1f}ms")


def example_sr():
    """forge_sr - Super resolution upscaling"""
    print("\n" + "="*60)
    print("Example 4: forge_sr - Super Resolution")
    print("="*60 + "\n")

    from vaultmind_forge.forge_sr import SuperResolutionUpscaler, SRBackend
    from PIL import Image

    # Create test image
    output_dir = Path("./output/quickstart")
    output_dir.mkdir(parents=True, exist_ok=True)

    test_img = output_dir / "test_lowres_sr.png"
    img = Image.new('RGB', (256, 256), color=(150, 100, 200))
    img.save(test_img)

    # Upscale image
    upscaler = SuperResolutionUpscaler()
    result = upscaler.upscale(
        input_path=test_img,
        output_path=output_dir / "test_upscaled.png",
        scale_factor=4,
        backend=SRBackend.FALLBACK_LANCZOS,
    )

    print(f"Upscaled image:")
    print(f"  From: {result.original_size}")
    print(f"  To: {result.upscaled_size}")
    print(f"  Backend: {result.backend_used.value}")
    print(f"  Time: {result.processing_time_ms:.1f}ms")


def example_video():
    """forge_video - Video generation"""
    print("\n" + "="*60)
    print("Example 5: forge_video - Video Generation")
    print("="*60 + "\n")

    from vaultmind_forge.forge_video import VideoGenerator, VideoConfig
    from PIL import Image

    # Create test frames
    output_dir = Path("./output/quickstart")
    output_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    for i in range(5):
        frame_path = output_dir / f"frame_{i:03d}.png"
        img = Image.new('RGB', (640, 480), color=(50*i, 100, 200-30*i))
        img.save(frame_path)
        frames.append(frame_path)

    # Create video
    generator = VideoGenerator()

    try:
        result = generator.frames_to_video(
            frame_paths=frames,
            output_path=output_dir / "test_video.mp4",
            config=VideoConfig(fps=2),
            frame_duration=1.0,
        )

        print(f"Video created:")
        print(f"  Frames: {result.frame_count}")
        print(f"  Duration: {result.duration_seconds:.1f}s")
        print(f"  Size: {result.file_size_mb:.2f} MB")
    except Exception as e:
        print(f"Video generation skipped (FFmpeg not available)")
        print(f"Error: {e}")


def example_versioning():
    """forge_versioning - Asset version control"""
    print("\n" + "="*60)
    print("Example 6: forge_versioning - Version Control")
    print("="*60 + "\n")

    from vaultmind_forge.forge_versioning import AssetVersionControl
    from PIL import Image

    # Create test asset
    output_dir = Path("./output/quickstart")
    output_dir.mkdir(parents=True, exist_ok=True)

    asset_path = output_dir / "character_v1.png"
    img = Image.new('RGB', (512, 512), color=(100, 150, 200))
    img.save(asset_path)

    # Initialize version control
    vcs = AssetVersionControl(repo_path=output_dir / "vcs_repo")

    # Commit asset
    version = vcs.commit(
        asset_path=asset_path,
        message="Initial character design",
        metadata={"iteration": 1}
    )

    print(f"Asset committed:")
    print(f"  Version ID: {version.version_id}")
    print(f"  Message: {version.message}")
    print(f"  Checksum: {version.checksum[:16]}...")

    # Create branch
    branch = vcs.create_branch("experimental", "Testing new style")
    print(f"\nBranch created: {branch.name}")

    # Get history
    history = vcs.get_history()
    print(f"\nVersion history: {len(history)} commits")


def example_style_presets():
    """forge_agent - Style presets"""
    print("\n" + "="*60)
    print("Example 7: forge_agent - Style Presets")
    print("="*60 + "\n")

    from vaultmind_forge.forge_agent import (
        get_style_preset,
        enhance_prompt_with_style,
        ALL_STYLES,
    )

    # List available styles
    print(f"Available styles: {len(ALL_STYLES)}")
    for name in list(ALL_STYLES.keys())[:5]:
        print(f"  - {name}")

    # Get style preset
    style = get_style_preset("cyberpunk")
    print(f"\nCyberpunk style:")
    print(f"  Guidance: {style.recommended_guidance}")
    print(f"  Steps: {style.recommended_steps}")

    # Enhance prompt
    prompts = enhance_prompt_with_style(
        "futuristic city",
        "cyberpunk"
    )

    print(f"\nEnhanced prompt:")
    print(f"  Positive: {prompts['positive'][:60]}...")
    print(f"  Negative: {prompts['negative'][:60]}...")


def example_metrics_analysis():
    """forge_monitor - Advanced metrics"""
    print("\n" + "="*60)
    print("Example 8: forge_monitor - Metrics Analysis")
    print("="*60 + "\n")

    from vaultmind_forge.forge_monitor import SystemMonitor, MetricsAggregator

    monitor = SystemMonitor()

    # Capture multiple snapshots
    for i in range(10):
        monitor.capture_snapshot()
        import time
        time.sleep(0.05)

    # Analyze metrics
    report = MetricsAggregator.generate_performance_report(monitor.snapshots)

    print(f"Performance analysis:")
    print(f"  CPU mean: {report['cpu']['stats']['mean']:.1f}%")
    print(f"  CPU trend: {report['cpu']['trend']}")
    print(f"  Memory mean: {report['memory']['stats']['mean']:.1f}%")
    print(f"  Anomalies: {report['cpu']['anomaly_count']}")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("  VaultMind Forge - Quick Start Examples")
    print("="*70)

    examples = [
        example_monitor,
        example_agent,
        example_semantic,
        example_sr,
        example_video,
        example_versioning,
        example_style_presets,
        example_metrics_analysis,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n  ⚠️  Example failed: {e}")

    print("\n" + "="*70)
    print("  All examples complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
