"""
Test Merlinv1 Integration with PromptRefinerExecutor

Quick test to verify:
1. Merlinv1Backend loads
2. PromptRefinerAgent uses Merlinv1
3. PromptRefinerExecutor works with the agent
"""

import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_merlinv1_backend():
    """Test 1: Merlinv1Backend loads"""
    print("\n" + "="*60)
    print("TEST 1: Merlinv1 Backend Loading")
    print("="*60)

    try:
        from vaultmind_forge.forge_ai.merlinv1_backend import Merlinv1Backend
        from vaultmind_forge.forge_ai.base_ai import AIRequest

        backend = Merlinv1Backend()
        backend.initialize()

        print(f"[OK] Merlinv1 loaded successfully")
        print(f"     Model path: {backend.model_path}")
        print(f"     Device: {backend.actual_device}")
        print(f"     Parameters: {backend.model.num_parameters():,}")

        # Quick generation test
        request = AIRequest(
            prompt="a majestic dragon",
            system_prompt="Enhance this prompt for image generation.",
            max_tokens=50,
            temperature=0.7
        )

        response = backend.generate(request)
        print(f"\n[OK] Test generation:")
        print(f"     Input: 'a majestic dragon'")
        print(f"     Output: {response.content[:100]}...")
        print(f"     Latency: {response.latency_ms:.0f}ms")

        backend.shutdown()
        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        return False

def test_prompt_refiner_agent():
    """Test 2: PromptRefinerAgent with Merlinv1"""
    print("\n" + "="*60)
    print("TEST 2: PromptRefinerAgent with Merlinv1")
    print("="*60)

    try:
        from vaultmind_forge.forge_agents.prompt_refiner import PromptRefinerAgent

        agent = PromptRefinerAgent(use_merlinv1=True)

        print(f"[OK] Agent created")
        print(f"     Merlinv1 available: {agent.merlinv1_available}")

        # Test refinement
        refinement = agent.refine_prompt(
            original_prompt="a cat sitting on a chair",
            style="photorealistic"
        )

        print(f"\n[OK] Prompt refined:")
        print(f"     Original: {refinement.original_prompt}")
        print(f"     Refined:  {refinement.refined_prompt}")
        print(f"     Confidence: {refinement.confidence:.2f}")
        print(f"     Reasoning: {refinement.reasoning}")

        # Shutdown Merlinv1 to free memory
        if agent.merlinv1_backend:
            agent.merlinv1_backend.shutdown()

        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prompt_refiner_executor():
    """Test 3: PromptRefinerExecutor node"""
    print("\n" + "="*60)
    print("TEST 3: PromptRefinerExecutor Node")
    print("="*60)

    try:
        from backend.executors.ai_nodes import PromptRefinerExecutor

        executor = PromptRefinerExecutor()

        print(f"[OK] Executor created: {executor.node_type}")

        # Test execution
        inputs = {
            "text": "a cyberpunk city at night",
            "style": "cinematic"
        }

        result = executor.execute(inputs)

        print(f"\n[OK] Execution result:")
        print(f"     Input: {inputs['text']}")
        print(f"     Style: {inputs['style']}")
        print(f"     Refined: {result['refined_prompt']}")
        print(f"     Method: {result['metadata']['method']}")
        print(f"     Model: {result['metadata']['model']}")
        print(f"     Confidence: {result['metadata'].get('confidence', 'N/A')}")

        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("MERLINV1 INTEGRATION TEST")
    print("="*60)

    results = []

    # Run tests
    results.append(("Merlinv1 Backend", test_merlinv1_backend()))
    results.append(("PromptRefinerAgent", test_prompt_refiner_agent()))
    results.append(("PromptRefinerExecutor", test_prompt_refiner_executor()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n[OK] All tests passed! Merlinv1 is integrated and working.")
    else:
        print("\n[WARN] Some tests failed. Check output above.")

    print("="*60)
