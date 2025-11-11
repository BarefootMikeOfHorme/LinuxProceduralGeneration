"""
VaultMind Forge - AI Integration Examples

Shows how to use the flexible AI backend system with different providers:
- Ollama (local, free)
- Claude API (cloud, paid)
- OpenAI API (cloud, paid)
- Hybrid mode (local primary, cloud fallback)
"""

from vaultmind_forge.forge_ai import (
    AIManager,
    create_ai_manager,
    AIBackend,
    AIRequest,
)


def example_1_ollama_local():
    """
    Example 1: Using Ollama (local, free)

    Requires:
    - Ollama installed (ollama.ai)
    - Model pulled: ollama pull llama3.2
    - pip install ollama
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Ollama (Local, Free)")
    print("=" * 70 + "\n")

    # Create AI manager with Ollama
    manager = create_ai_manager(
        mode="local",
        ollama_model="llama3.2",  # or "mistral", "phi3", etc.
    )

    try:
        manager.initialize()
        print("[OK] Ollama initialized")
    except Exception as e:
        print(f"[ERROR] Ollama not available: {e}")
        print("\nTo use Ollama:")
        print("  1. Install: Download from ollama.ai")
        print("  2. Pull model: ollama pull llama3.2")
        print("  3. Install Python package: pip install ollama")
        return

    # Create request
    request = AIRequest(
        prompt="Generate a creative description for a legendary sword with magical properties.",
        system_prompt="You are a fantasy game asset designer.",
        max_tokens=200,
        temperature=0.7,
    )

    print("Generating response...")
    response = manager.generate(request)

    print(f"\nResponse:")
    print(f"  {response.content[:200]}...")
    print(f"\nStats:")
    print(f"  Backend: {response.backend}")
    print(f"  Model: {response.model}")
    print(f"  Tokens: {response.tokens_used}")
    print(f"  Latency: {response.latency_ms:.0f}ms")
    print(f"  Cost: ${response.cost_estimate:.4f} (FREE)")

    manager.shutdown()


def example_2_claude_cloud():
    """
    Example 2: Using Claude API (cloud, paid)

    Requires:
    - Anthropic API key
    - pip install anthropic
    - Set ANTHROPIC_API_KEY environment variable
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Claude API (Cloud, Paid)")
    print("=" * 70 + "\n")

    # Create AI manager with Claude
    manager = create_ai_manager(
        mode="cloud",
        backend="claude",
        claude_model="claude-3-5-haiku-20241022",  # Cheaper model
        # claude_api_key="your-key-here"  # Or set ANTHROPIC_API_KEY env var
    )

    try:
        manager.initialize()
        print("[OK] Claude initialized")
    except Exception as e:
        print(f"[ERROR] Claude not available: {e}")
        print("\nTo use Claude:")
        print("  1. Get API key: console.anthropic.com")
        print("  2. Install: pip install anthropic")
        print("  3. Set env var: export ANTHROPIC_API_KEY=your-key")
        return

    # Create request
    request = AIRequest(
        prompt="Generate a detailed material specification for a sci-fi armor texture.",
        system_prompt="You are an expert in game asset material configuration.",
        max_tokens=300,
    )

    print("Generating response...")
    response = manager.generate(request)

    print(f"\nResponse:")
    print(f"  {response.content[:200]}...")
    print(f"\nStats:")
    print(f"  Backend: {response.backend}")
    print(f"  Model: {response.model}")
    print(f"  Tokens: {response.tokens_used}")
    print(f"  Latency: {response.latency_ms:.0f}ms")
    print(f"  Cost: ${response.cost_estimate:.4f}")

    manager.shutdown()


def example_3_hybrid_mode():
    """
    Example 3: Hybrid Mode (local primary, cloud fallback)

    Best of both worlds:
    - Try Ollama first (free)
    - Fall back to Claude if Ollama fails (paid backup)
    - Optimal cost savings (80% local, 20% cloud)
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Hybrid Mode (Local + Cloud Fallback)")
    print("=" * 70 + "\n")

    # Create hybrid AI manager
    manager = create_ai_manager(
        mode="hybrid",
        ollama_model="llama3.2",
        claude_model="claude-3-5-haiku-20241022",
        # claude_api_key="your-key-here"
    )

    try:
        manager.initialize()
        print("[OK] Hybrid manager initialized")
        print("  Primary: Ollama (local, free)")
        print("  Fallback: Claude (cloud, paid)")
    except Exception as e:
        print(f"[ERROR] Initialization failed: {e}")
        return

    # Test multiple requests
    print("\nSending 3 requests...")

    for i in range(3):
        request = AIRequest(
            prompt=f"Generate a short name for a fantasy {['weapon', 'armor', 'potion'][i]}.",
            max_tokens=50,
        )

        response = manager.generate(request)
        print(f"\n  Request {i+1}:")
        print(f"    Backend used: {response.backend}")
        print(f"    Result: {response.content[:50]}")
        print(f"    Cost: ${response.cost_estimate:.4f}")

    # Show stats
    stats = manager.get_stats()
    print(f"\nManager Stats:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Primary requests: {stats['primary_requests']} (free)")
    print(f"  Fallback requests: {stats['fallback_requests']} (paid)")
    print(f"  Fallback rate: {stats['fallback_rate']:.0%}")

    manager.shutdown()


def example_4_manual_backend_selection():
    """
    Example 4: Manual backend creation and selection

    For advanced use cases where you want full control.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Manual Backend Selection")
    print("=" * 70 + "\n")

    # Create manager with specific configuration
    manager = AIManager(
        primary_backend=AIBackend.OLLAMA,
        fallback_backend=AIBackend.CLAUDE,
        ollama_model="mistral",  # Use Mistral instead of Llama
        ollama_url="http://localhost:11434",
        claude_model="claude-3-5-sonnet-20241022",  # Use Sonnet for better quality
    )

    try:
        manager.initialize()
        print("[OK] Custom manager initialized")
        print(f"  Primary: Ollama (Mistral)")
        print(f"  Fallback: Claude (Sonnet 3.5)")
    except Exception as e:
        print(f"[ERROR] {e}")
        return

    request = AIRequest(
        prompt="Explain the PBR workflow for game textures in 2 sentences.",
        max_tokens=100,
    )

    response = manager.generate(request)
    print(f"\nResponse: {response.content}")
    print(f"Backend: {response.backend} ({response.model})")

    manager.shutdown()


def example_5_cost_comparison():
    """
    Example 5: Cost comparison between backends

    Shows the cost difference between local and cloud backends.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Cost Comparison")
    print("=" * 70 + "\n")

    print("Estimated costs for 1000 requests (avg 500 tokens):")
    print()

    # Ollama (local)
    print("Ollama (Local):")
    print("  Cost: $0.00 (FREE)")
    print("  Latency: ~100-500ms per request")
    print("  Pros: Free, private, offline")
    print("  Cons: Requires local GPU/CPU, quality varies")
    print()

    # Claude Haiku (cheapest cloud)
    haiku_cost = (500 / 1_000_000) * 0.8 * 1000  # Input
    haiku_cost += (200 / 1_000_000) * 4.0 * 1000  # Output (est 200 tokens)
    print("Claude Haiku (Cloud):")
    print(f"  Cost: ${haiku_cost:.2f}")
    print("  Latency: ~200-800ms per request")
    print("  Pros: High quality, no setup")
    print("  Cons: Paid, requires internet")
    print()

    # Claude Sonnet (best quality)
    sonnet_cost = (500 / 1_000_000) * 3.0 * 1000
    sonnet_cost += (200 / 1_000_000) * 15.0 * 1000
    print("Claude Sonnet (Cloud):")
    print(f"  Cost: ${sonnet_cost:.2f}")
    print("  Latency: ~300-1000ms per request")
    print("  Pros: Best quality")
    print("  Cons: Most expensive")
    print()

    # Hybrid (80% local, 20% cloud)
    hybrid_cost = haiku_cost * 0.2  # Only 20% go to cloud
    print("Hybrid (80% Ollama, 20% Claude Haiku):")
    print(f"  Cost: ${hybrid_cost:.2f}")
    print("  Savings: {:.0%} vs cloud-only".format(1 - (hybrid_cost / haiku_cost)))
    print("  Pros: Best cost/quality balance")
    print("  Cons: Requires both setups")


def main():
    """Run all examples"""
    print("\n" + "*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  VaultMind Forge - AI Integration Examples".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)

    print("\nThis demo shows flexible AI backend integration:")
    print("  - Ollama (local, free)")
    print("  - Claude API (cloud, paid)")
    print("  - OpenAI API (cloud, paid)")
    print("  - Hybrid mode (best of both)")

    # Run examples
    example_1_ollama_local()
    # example_2_claude_cloud()  # Uncomment if you have API key
    # example_3_hybrid_mode()    # Uncomment if you have API key
    example_4_manual_backend_selection()
    example_5_cost_comparison()

    print("\n" + "=" * 70)
    print("SUMMARY: AI Integration Complete")
    print("=" * 70)
    print("""
The AI integration system is complete and supports:

BACKENDS:
  1. Ollama (local) - FREE, private, offline
  2. Claude API - High quality, paid
  3. OpenAI API - Good ecosystem, paid
  4. Hybrid mode - Best cost/performance

RECOMMENDATIONS:
  - Development: Use Ollama (free)
  - Production (cost-sensitive): Use Hybrid (80% savings)
  - Production (quality-focused): Use Claude/OpenAI
  - Enterprise: Use Hybrid with custom fallback logic

USAGE IN VAULTMIND FORGE:
  The agents will automatically use the configured AI backend
  when they need to escalate complex decisions. In most cases
  (75%), agents handle decisions autonomously without AI calls.

  When AI is needed:
  - Complex prompt generation
  - Ambiguous quality assessment
  - Multi-step planning
  - Custom requirement interpretation

NEXT STEPS:
  1. Choose your backend (Ollama recommended for start)
  2. Install dependencies (see examples above)
  3. Configure in pipeline (coming next)
  4. Run end-to-end generation!
    """)


if __name__ == "__main__":
    main()
