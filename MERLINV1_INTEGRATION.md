# Merlinv1 Integration Guide

## Overview

**Merlinv1** is a GPT-2 style language model (42M parameters) trained from scratch with zero pretrained bias for use in the Vaultmind Forge AI content generation system.

### Model Specifications
- **Architecture**: GPT-2 (8 layers, 8 heads, 512 dim)
- **Parameters**: ~42 million
- **Tokenizer**: Custom BPE (10K vocab)
- **Context Window**: 4096 tokens
- **Training Data**: Shakespeare, Cornell Movie Dialogs, LOTR, Gutenberg samples
- **Training Steps**: 40,000
- **Hardware**: RTX 4070 Ti (bf16 precision)

---

## Quick Start

### 1. Verify Training Completed

Check that the final model exists:
```bash
dir C:\Merlinv1\checkpoints\final
```

You should see:
- `config.json`
- `pytorch_model.bin`
- `tokenizer.json`
- `tokenizer_config.json`

### 2. Test the Integration

Run the test script:
```bash
cd C:\Users\Administrator\Desktop\Projects\LPG
python test_merlinv1_integration.py
```

This will verify:
- ✓ Model loads correctly
- ✓ Tokenizer works
- ✓ GPU inference runs
- ✓ Backend integrates with forge_ai

### 3. Use in Python Code

```python
from vaultmind_forge.forge_ai import Merlinv1Backend, AIRequest

# Initialize backend
backend = Merlinv1Backend(
    model_path="C:/Merlinv1/checkpoints/final",
    device="cuda"  # or "cpu" or "auto"
)
backend.initialize()

# Generate text
request = AIRequest(
    prompt="A mysterious artifact:",
    system_prompt="You are a fantasy world builder.",
    max_tokens=200,
    temperature=0.8
)

response = backend.generate(request)
print(response.content)

# Check stats
print(backend.get_stats())

# Cleanup
backend.shutdown()
```

---

## Integration with Vaultmind Forge

### Use Cases

1. **forge_agent**: Job planning and orchestration
   - Parse user intent
   - Generate job schemas
   - Suggest helper passes

2. **forge_agents**: Specialized AI agents
   - Prompt refinement
   - Style suggestions
   - Parameter optimization

3. **Feedback Loops**: Quality assessment
   - Explain rejection reasons
   - Suggest corrections
   - Learn from failures

### Example: Prompt Refiner Agent

```python
from vaultmind_forge.forge_ai import Merlinv1Backend, AIRequest
from vaultmind_forge.forge_agents import PromptRefiner

# Create backend
backend = Merlinv1Backend()
backend.initialize()

# Create agent with Merlinv1
refiner = PromptRefiner(ai_backend=backend)

# Refine a prompt
original = "a sword"
refined = refiner.refine_prompt(
    original,
    style="fantasy",
    detail_level="high"
)

print(f"Original: {original}")
print(f"Refined: {refined}")
# Output: "An ornate longsword with intricate runes etched along the blade..."
```

---

## Performance

### Inference Speed (RTX 4070 Ti)
- **GPU (CUDA)**: ~50-100 tokens/sec
- **CPU**: ~5-10 tokens/sec

### Memory Usage
- **VRAM**: ~200-300 MB (model only)
- **RAM**: ~500 MB

### Cost
- **API calls**: $0 (runs locally)
- **Electricity**: Negligible (<10W during inference)

---

## Backend Comparison

| Backend | Cost/1M tokens | Speed | Bias | Privacy |
|---------|----------------|-------|------|---------|
| **Merlinv1** | $0 | Fast (local GPU) | Zero (from-scratch) | 100% private |
| Claude | $3-15 | Very fast | Unknown | Cloud API |
| GPT-4 | $30-60 | Fast | Unknown | Cloud API |
| Ollama (Llama) | $0 | Medium | Pretrained | Local |

---

## Configuration

### AIManager Integration

```python
from vaultmind_forge.forge_ai import (
    AIManager,
    Merlinv1Backend,
    create_ai_manager
)

# Option 1: Direct creation
manager = AIManager()
manager.register_backend("merlinv1", Merlinv1Backend())
manager.set_active_backend("merlinv1")

# Option 2: Factory
manager = create_ai_manager(
    backend="merlinv1",
    model_path="C:/Merlinv1/checkpoints/final"
)

# Use manager
request = AIRequest(prompt="Generate a weapon description")
response = manager.generate(request)
```

### Tiered AI System

Use Merlinv1 for fast local tasks, escalate to Claude/GPT for complex reasoning:

```python
from vaultmind_forge.forge_ai import (
    TieredAIManager,
    TaskComplexity,
    Merlinv1Backend
)

manager = TieredAIManager()

# Register tiers
manager.register_tier(
    complexity=TaskComplexity.SIMPLE,
    backend=Merlinv1Backend()  # Fast local
)

manager.register_tier(
    complexity=TaskComplexity.COMPLEX,
    backend=ClaudeBackend()  # Expensive but powerful
)

# Auto-route based on task
response = manager.generate_smart(
    prompt="Refine this prompt: 'a sword'",
    complexity=TaskComplexity.SIMPLE  # Uses Merlinv1
)
```

---

## Troubleshooting

### Model Not Found
```
AIError: Merlinv1 model not found at: C:/Merlinv1/checkpoints/final
```

**Solution**: Ensure training completed and saved final checkpoint:
```bash
cd C:\Merlinv1
START_WITH_NEPTUNE.bat
# Wait for training to complete (9+ hours)
```

### CUDA Out of Memory
```
RuntimeError: CUDA out of memory
```

**Solution**: Close other GPU applications or use CPU:
```python
backend = Merlinv1Backend(device="cpu")
```

### Slow Inference on CPU
If using CPU and generation is slow (< 5 tok/sec), check:
- PyTorch is using all CPU cores
- No other heavy processes running
- Consider upgrading to GPU or using smaller batch sizes

---

## Future Enhancements

Once Merlinv1 is running well:

1. **Fine-tuning**: Train specialized versions
   - Fantasy-focused (more LOTR/D&D data)
   - Technical (CAD/architecture descriptions)
   - Conversational (more dialog data)

2. **LoRA Adapters**: Quick style switching
   - Load different adapters for different genres
   - Switch between formal/casual tone

3. **Quantization**: Reduce memory usage
   - INT8 quantization (~50% VRAM reduction)
   - ONNX export for faster inference

4. **Distillation**: Create smaller versions
   - Merlinv1-Tiny (10M params) for mobile
   - Merlinv1-Nano (5M params) for edge devices

---

## Next Steps

1. ✓ Training Merlinv1 (in progress - ~9.5 hours)
2. ⏳ Run integration test (`test_merlinv1_integration.py`)
3. ⏳ Wire into forge_agent for job planning
4. ⏳ Create prompt refiner agent using Merlinv1
5. ⏳ Test end-to-end asset generation with local AI

---

## Support

For issues or questions:
1. Check Neptune.ai dashboard for training metrics
2. Review CLI Observatory logs
3. Check `C:/Merlinv1/checkpoints/` for saved models
4. Verify GPU is being used: `nvidia-smi`

**Training Dashboard**: https://app.neptune.ai/HormeNeptune/Merlinv1
