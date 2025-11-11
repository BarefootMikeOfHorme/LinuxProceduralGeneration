"""
VaultMind Forge - GPT-20B Planner + FLUX Integration

Complete example showing:
- GPT-20B for complex planning
- FLUX.1 + LoRA for image generation
- Automatic model load/unload sequencing
- Memory-efficient multi-model workflow

Workflow:
1. Load GPT-20B → Plan generation strategy
2. Unload GPT-20B, Load FLUX → Generate images
3. Load GPT-20B → Evaluate results
4. Optimize based on feedback
"""

import torch
from pathlib import Path

from vaultmind_forge.forge_ai import (
    ModelManager,
    ModelConfig,
    ModelRole,
    create_flux_loader,
    create_gpt_loader,
    GPTPlannerBackend,
    AIRequest,
)


def example_1_basic_sequencing():
    """
    Example 1: Basic model sequencing

    Shows automatic load/unload as you switch between models.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Model Sequencing")
    print("=" * 70 + "\n")

    # Create model manager (24GB VRAM budget)
    manager = ModelManager(
        max_total_memory_gb=24.0,
        auto_unload=True,
        unload_delay=30.0,  # Unload after 30s idle
    )

    # Register GPT-20B planner
    manager.register_model(ModelConfig(
        name="gpt-planner",
        role=ModelRole.PLANNER,
        model_path="openai/gpt-oss-20b",
        loader_func=create_gpt_loader(),
        max_memory_gb=12.0,
        priority=10,  # High priority
        torch_dtype=torch.float16,
    ))

    # Register FLUX diffusion with LoRA
    manager.register_model(ModelConfig(
        name="flux-diffusion",
        role=ModelRole.DIFFUSION,
        model_path="black-forest-labs/FLUX.1-dev",
        loader_func=create_flux_loader(),
        max_memory_gb=8.0,
        priority=5,
        torch_dtype=torch.float16,
        lora_weights={
            "uncensored": "Heartsync/Flux-NSFW-uncensored"
        }
    ))

    print("Models registered:")
    for name, status in manager.models.items():
        print(f"  - {name}: {status.config.role.value} "
              f"({status.config.max_memory_gb}GB)")

    # Step 1: Use GPT planner for strategy
    print("\n[STEP 1] Using GPT planner for generation strategy...")
    with manager.use_model("gpt-planner") as planner_dict:
        planner = planner_dict["model"]
        tokenizer = planner_dict["tokenizer"]

        prompt = """Plan a generation strategy for a high-quality fantasy character texture.
Consider: resolution, detail level, material types, and generation parameters."""

        inputs = tokenizer(prompt, return_tensors="pt").to(planner.device)

        with torch.no_grad():
            outputs = planner.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True,
            )

        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Plan: {result[:200]}...")

    print(f"\nCurrent memory usage: {manager.get_total_memory_usage():.1f}GB")
    print(f"Loaded models: {manager.get_loaded_models()}")

    # Step 2: Use FLUX for generation
    print("\n[STEP 2] Using FLUX for image generation...")
    print("(GPT will be auto-unloaded to free memory)")

    with manager.use_model("flux-diffusion") as pipe:
        prompt = "A woman in a sheer white dress standing on a beach at sunset, " \
                 "backlit so her silhouette is visible through the thin fabric, " \
                 "shot with Canon EOS R5, 85mm f/1.2 lens, golden hour natural lighting, " \
                 "professional composition, hyperrealistic detail, masterpiece quality, 8K"

        negative_prompt = "text, watermark, signature, cartoon, anime, " \
                         "illustration, painting, drawing, low quality, blurry"

        seed = 42
        generator = torch.Generator(device="cuda").manual_seed(seed)

        image = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            guidance_scale=7.0,
            num_inference_steps=28,
            width=1024,
            height=1024,
            generator=generator,
        ).images[0]

        # Save image
        output_path = Path("output/gpt_planner_example_1.png")
        output_path.parent.mkdir(exist_ok=True)
        image.save(output_path)
        print(f"Image saved: {output_path}")

    print(f"\nCurrent memory usage: {manager.get_total_memory_usage():.1f}GB")
    print(f"Loaded models: {manager.get_loaded_models()}")

    # Step 3: Use GPT for evaluation
    print("\n[STEP 3] Using GPT for quality evaluation...")
    with manager.use_model("gpt-planner") as planner_dict:
        planner = planner_dict["model"]
        tokenizer = planner_dict["tokenizer"]

        eval_prompt = f"""Evaluate this generation result:
Prompt: {prompt}
Output: 1024x1024 image, seed={seed}

Provide quality assessment and improvement suggestions."""

        inputs = tokenizer(eval_prompt, return_tensors="pt").to(planner.device)

        with torch.no_grad():
            outputs = planner.generate(**inputs, max_new_tokens=150)

        evaluation = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Evaluation: {evaluation[:200]}...")

    print("\n[OK] Sequence complete!")
    print(f"Final stats: {manager.get_stats()}")

    manager.shutdown()


def example_2_integrated_backend():
    """
    Example 2: Using GPTPlannerBackend

    Simplified interface with automatic ModelManager integration.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: GPT Planner Backend")
    print("=" * 70 + "\n")

    # Create GPT planner backend (auto-creates ModelManager)
    planner = GPTPlannerBackend(
        model="openai/gpt-oss-20b",
        max_memory_gb=12.0,
        keep_loaded=False,  # Auto-unload when idle
    )

    planner.initialize()
    print(f"[OK] GPT planner initialized")

    # Test planning request
    request = AIRequest(
        prompt="Plan a batch generation strategy for 10 character textures "
               "with varying quality levels (3 hero, 5 standard, 2 background). "
               "Optimize for memory efficiency and generation time.",
        system_prompt="You are an expert game asset pipeline planner. "
                      "Provide concise, actionable plans.",
        max_tokens=300,
        temperature=0.7,
    )

    print("\nGenerating plan...")
    response = planner.generate(request)

    print(f"\nPlan:")
    print(f"{response.content}\n")

    print(f"Stats:")
    print(f"  Tokens: {response.tokens_used}")
    print(f"  Latency: {response.latency_ms:.0f}ms")
    print(f"  Cost: ${response.cost_estimate:.4f}")

    # Get model stats
    stats = planner.get_model_stats()
    print(f"\nModel stats:")
    if "model_status" in stats:
        print(f"  State: {stats['model_status']['state']}")
        print(f"  Memory: {stats['model_status']['memory_usage_gb']:.1f}GB")
        print(f"  Load count: {stats['model_status']['load_count']}")

    planner.shutdown()


def example_3_hybrid_workflow():
    """
    Example 3: Complete hybrid workflow

    GPT-20B planner + Ollama helpers + FLUX diffusion
    Shows real-world usage with multiple models.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Hybrid Workflow (GPT + Ollama + FLUX)")
    print("=" * 70 + "\n")

    from vaultmind_forge.forge_ai import create_ai_manager, AIBackend

    # Create shared ModelManager
    model_manager = ModelManager(
        max_total_memory_gb=24.0,
        auto_unload=True,
        unload_delay=60.0,
    )

    # Register FLUX
    model_manager.register_model(ModelConfig(
        name="flux-diffusion",
        role=ModelRole.DIFFUSION,
        model_path="black-forest-labs/FLUX.1-dev",
        loader_func=create_flux_loader(),
        max_memory_gb=8.0,
        lora_weights={"uncensored": "Heartsync/Flux-NSFW-uncensored"}
    ))

    # Create AI manager (Ollama primary, GPT planner fallback)
    # Note: For complex planning, we'll explicitly use GPT
    ai_manager = create_ai_manager(
        mode="local",  # Start with Ollama for simple tasks
        ollama_model="llama3.2"
    )
    ai_manager.initialize()

    # Create GPT planner (shares ModelManager)
    gpt_planner = GPTPlannerBackend(
        model="openai/gpt-oss-20b",
        model_manager=model_manager,
        max_memory_gb=12.0,
    )
    gpt_planner.initialize()

    print("Workflow initialized:")
    print("  - Ollama (helper): Simple tasks, classifications")
    print("  - GPT-20B (planner): Complex planning, strategy")
    print("  - FLUX (diffusion): Image generation")

    # Workflow: Generate a hero character
    print("\n[WORKFLOW] Generating hero character texture\n")

    # Step 1: Use helper AI for quick classification
    print("Step 1: Classify asset requirements (Ollama)...")
    helper_request = AIRequest(
        prompt="Classify this asset: 'hero character with ornate armor'. "
               "Return: category, importance, estimated_resolution",
        max_tokens=50,
    )
    helper_response = ai_manager.generate(helper_request)
    print(f"  → {helper_response.content[:100]}")

    # Step 2: Use GPT planner for strategy
    print("\nStep 2: Plan generation strategy (GPT-20B)...")
    plan_request = AIRequest(
        prompt="Plan the generation of a hero character with ornate armor. "
               "Include: resolution, detail level, material setup, generation params.",
        system_prompt="You are a game asset expert. Be concise.",
        max_tokens=200,
    )
    plan_response = gpt_planner.generate(plan_request)
    print(f"  → Plan: {plan_response.content[:150]}...")

    # Step 3: Generate with FLUX
    print("\nStep 3: Generate image (FLUX)...")
    print("  (Auto-unloading GPT-20B to free memory...)")

    with model_manager.use_model("flux-diffusion") as pipe:
        image = pipe(
            prompt="ornate fantasy armor character, detailed metalwork, "
                   "photorealistic, 8K, masterpiece",
            negative_prompt="blurry, low quality",
            num_inference_steps=28,
            width=1024,
            height=1024,
        ).images[0]

        output_path = Path("output/gpt_planner_hero_character.png")
        output_path.parent.mkdir(exist_ok=True)
        image.save(output_path)
        print(f"  → Saved: {output_path}")

    # Step 4: Quality check (Ollama - quick check)
    print("\nStep 4: Quick quality check (Ollama)...")
    quality_request = AIRequest(
        prompt="Quick quality checklist for hero character texture: "
               "resolution OK, detail level OK, armor visible?",
        max_tokens=50,
    )
    quality_response = ai_manager.generate(quality_request)
    print(f"  → {quality_response.content[:100]}")

    print("\n[OK] Workflow complete!")
    print(f"\nMemory stats: {model_manager.get_stats()}")

    # Cleanup
    model_manager.shutdown()
    ai_manager.shutdown()
    gpt_planner.shutdown()


def example_4_memory_optimization():
    """
    Example 4: Memory optimization strategies

    Shows different strategies for constrained memory.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Memory Optimization Strategies")
    print("=" * 70 + "\n")

    # Strategy 1: Aggressive auto-unload (tight memory)
    print("Strategy 1: Aggressive unload (16GB VRAM)")
    manager_tight = ModelManager(
        max_total_memory_gb=16.0,
        auto_unload=True,
        unload_delay=10.0,  # Unload quickly
    )

    manager_tight.register_model(ModelConfig(
        name="gpt-planner",
        role=ModelRole.PLANNER,
        model_path="openai/gpt-oss-20b",
        loader_func=create_gpt_loader(),
        max_memory_gb=12.0,
        priority=10,
        keep_loaded=False,  # Don't keep loaded
    ))

    manager_tight.register_model(ModelConfig(
        name="flux-diffusion",
        role=ModelRole.DIFFUSION,
        model_path="black-forest-labs/FLUX.1-dev",
        loader_func=create_flux_loader(),
        max_memory_gb=8.0,
        priority=8,
        keep_loaded=False,
    ))

    print("  - Max memory: 16GB")
    print("  - Unload delay: 10s")
    print("  - Keep loaded: False")
    print("  → Models unload immediately after use\n")

    # Strategy 2: Keep planner loaded (frequent planning)
    print("Strategy 2: Keep planner loaded (24GB VRAM)")
    manager_planner_focus = ModelManager(
        max_total_memory_gb=24.0,
        auto_unload=True,
        unload_delay=60.0,
    )

    manager_planner_focus.register_model(ModelConfig(
        name="gpt-planner",
        role=ModelRole.PLANNER,
        model_path="openai/gpt-oss-20b",
        loader_func=create_gpt_loader(),
        max_memory_gb=12.0,
        priority=10,
        keep_loaded=True,  # Always loaded
    ))

    print("  - Max memory: 24GB")
    print("  - Planner: Keep loaded (frequent use)")
    print("  - Diffusion: Auto-unload")
    print("  → Faster planning, diffusion loads on-demand\n")

    # Strategy 3: Priority-based (mixed workload)
    print("Strategy 3: Priority-based eviction (20GB VRAM)")
    manager_priority = ModelManager(
        max_total_memory_gb=20.0,
        auto_unload=True,
        unload_delay=30.0,
    )

    manager_priority.register_model(ModelConfig(
        name="gpt-planner",
        role=ModelRole.PLANNER,
        model_path="openai/gpt-oss-20b",
        loader_func=create_gpt_loader(),
        max_memory_gb=12.0,
        priority=10,  # High priority (last to unload)
    ))

    manager_priority.register_model(ModelConfig(
        name="flux-diffusion",
        role=ModelRole.DIFFUSION,
        model_path="black-forest-labs/FLUX.1-dev",
        loader_func=create_flux_loader(),
        max_memory_gb=8.0,
        priority=5,  # Lower priority (first to unload)
    ))

    print("  - Max memory: 20GB")
    print("  - Priority-based eviction:")
    print("    - Planner: priority=10 (high)")
    print("    - Diffusion: priority=5 (lower)")
    print("  → Planner stays longer, diffusion unloads first\n")

    print("[OK] Memory strategies demonstrated")

    # Cleanup
    manager_tight.shutdown()
    manager_planner_focus.shutdown()
    manager_priority.shutdown()


def main():
    """Run all examples"""
    print("\n" + "*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  VaultMind Forge - GPT-20B Planner Integration".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)

    print("""
This demo shows:
  - GPT-20B for complex planning and reasoning
  - FLUX.1 + LoRA for image generation
  - Automatic model load/unload sequencing
  - Memory-efficient multi-model workflows

ModelManager automatically:
  ✓ Loads models on-demand
  ✓ Unloads idle models to free memory
  ✓ Handles priority-based eviction
  ✓ Thread-safe concurrent access
    """)

    # Run examples
    try:
        example_1_basic_sequencing()
    except Exception as e:
        print(f"[ERROR] Example 1 failed: {e}")

    try:
        example_2_integrated_backend()
    except Exception as e:
        print(f"[ERROR] Example 2 failed: {e}")

    try:
        example_3_hybrid_workflow()
    except Exception as e:
        print(f"[ERROR] Example 3 failed: {e}")

    try:
        example_4_memory_optimization()
    except Exception as e:
        print(f"[ERROR] Example 4 failed: {e}")

    print("\n" + "=" * 70)
    print("SUMMARY: GPT-20B Planner Integration")
    print("=" * 70)
    print("""
COMPLETE SYSTEM:
  ✓ ModelManager - Thread-safe load/unload sequencer
  ✓ GPTPlannerBackend - GPT-20B for complex planning
  ✓ FLUX integration - With LoRA support
  ✓ Automatic memory management
  ✓ Priority-based model eviction

USAGE PATTERNS:
  1. Planning-heavy: Keep GPT-20B loaded, unload diffusion
  2. Generation-heavy: Keep FLUX loaded, unload planner
  3. Balanced: Auto-unload both based on usage
  4. Memory-constrained: Aggressive auto-unload (10s delay)

INTEGRATION WITH VAULTMIND FORGE:
  - Agents use helper AI (Ollama) for 80% of decisions
  - GPT-20B handles complex 20% (escalated decisions)
  - FLUX generates final images
  - Total cost: ~95% savings vs GPT-only pipeline

NEXT STEPS:
  1. Test with your GPT-20B model
  2. Tune memory limits for your hardware
  3. Integrate with agent pipeline
  4. Add more models (SDXL, SD3, etc.)
    """)


if __name__ == "__main__":
    main()
