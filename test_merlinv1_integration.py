"""
Test Merlinv1 Integration with Vaultmind Forge

Run this after Merlinv1 training completes to verify:
1. Model loads correctly
2. Tokenizer works
3. Inference runs on GPU/CPU
4. Backend integrates with forge_ai system
"""

import sys
from pathlib import Path

# Add vaultmind_forge to path
sys.path.insert(0, str(Path(__file__).parent / "vaultmind_forge"))

from forge_ai import Merlinv1Backend, AIRequest

def test_merlinv1():
    print("="*70)
    print("MERLINV1 INTEGRATION TEST")
    print("="*70)
    print()

    # Test 1: Initialize backend
    print("[1/4] Initializing Merlinv1 backend...")
    try:
        backend = Merlinv1Backend(
            model_path="C:/Merlinv1/checkpoints/final",
            device="auto"
        )
        backend.initialize()
        print(f"✓ Backend initialized")
        print(f"  Device: {backend.actual_device}")
        print(f"  Model params: {backend.model.num_parameters():,}")
        print()
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False

    # Test 2: Check availability
    print("[2/4] Checking backend availability...")
    if backend.is_available():
        print("✓ Backend is available")
        print()
    else:
        print("✗ Backend not available")
        return False

    # Test 3: Simple generation
    print("[3/4] Testing simple generation...")
    try:
        request = AIRequest(
            prompt="The ancient sword",
            max_tokens=100,
            temperature=0.8
        )

        response = backend.generate(request)

        print(f"✓ Generation successful")
        print(f"  Input: {request.prompt}")
        print(f"  Output: {response.content[:200]}...")
        print(f"  Tokens: {response.tokens_used}")
        print(f"  Latency: {response.latency_ms:.0f}ms")
        print(f"  Device: {response.metadata['device']}")
        print()
    except Exception as e:
        print(f"✗ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 4: System prompt + generation
    print("[4/4] Testing with system prompt...")
    try:
        request = AIRequest(
            system_prompt="You are a fantasy world builder. Describe items with vivid detail.",
            prompt="A mysterious artifact found in ancient ruins:",
            max_tokens=150,
            temperature=0.9
        )

        response = backend.generate(request)

        print(f"✓ System prompt generation successful")
        print(f"  Output: {response.content[:200]}...")
        print(f"  Tokens: {response.tokens_used}")
        print(f"  Latency: {response.latency_ms:.0f}ms")
        print()
    except Exception as e:
        print(f"✗ System prompt generation failed: {e}")
        return False

    # Stats
    print("="*70)
    print("BACKEND STATISTICS")
    print("="*70)
    stats = backend.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()

    # Cleanup
    print("Shutting down backend...")
    backend.shutdown()
    print("✓ Shutdown complete")
    print()

    print("="*70)
    print("ALL TESTS PASSED! ✓")
    print("="*70)
    print()
    print("Merlinv1 is ready to use in Vaultmind Forge!")
    print()
    print("Next steps:")
    print("1. Integrate with forge_agent for job planning")
    print("2. Use for prompt refinement and style suggestions")
    print("3. Enable AI-assisted feedback loops")
    print()

    return True


if __name__ == "__main__":
    print()
    print("Prerequisites:")
    print("- Merlinv1 training completed")
    print("- Final model saved to: C:/Merlinv1/checkpoints/final")
    print("- PyTorch + transformers installed")
    print()
    input("Press Enter to start test...")
    print()

    success = test_merlinv1()

    if not success:
        print()
        print("Test failed! Check error messages above.")
        print()
        print("Common issues:")
        print("- Model not trained yet (run: START_WITH_NEPTUNE.bat)")
        print("- Wrong model path (check: C:/Merlinv1/checkpoints/final)")
        print("- Missing dependencies (pip install transformers torch)")
        sys.exit(1)
