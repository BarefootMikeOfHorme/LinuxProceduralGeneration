"""
Unified Agent Backend - TeichAI GPT-OSS-20B + Claude 4.5 Sonnet Distill

Single powerful model combining:
- GPT-20B (20 billion parameters)
- Claude 4.5 Sonnet (high reasoning distillation)

This unified model replaces both:
- oh-dcft-v3.1 (executive function)
- GPT-20B (planning)

Benefits:
- One model for 95% of AI calls (only Ollama helper for simple 5%)
- High reasoning capability (Claude 4.5 Sonnet)
- Deep planning (GPT-20B)
- Tool use and executive function
- Simpler architecture (2-tier instead of 3-tier)
"""

from __future__ import annotations

import time
import logging
from typing import Optional, Dict, Any

import torch

from .base_ai import BaseAI, AIRequest, AIResponse, AIError
from .model_manager import ModelManager, ModelConfig, ModelRole

logger = logging.getLogger(__name__)


class UnifiedAgentBackend(BaseAI):
    """
    Unified agent backend using TeichAI's hybrid model.

    Combines GPT-20B and Claude 4.5 Sonnet in single model.
    Handles both executive function and deep reasoning.

    Example:
        >>> # Option 1: Use existing ModelManager
        >>> manager = ModelManager(max_total_memory_gb=24.0)
        >>> backend = UnifiedAgentBackend(model_manager=manager)
        >>> backend.initialize()
        >>>
        >>> # Option 2: Create standalone
        >>> backend = UnifiedAgentBackend(
        ...     model="TeichAI/gpt-oss-20b-claude-4.5-sonnet-high-reasoning-distill-GGUF"
        ... )
        >>> backend.initialize()
        >>>
        >>> # Handles both simple and complex tasks
        >>> simple_request = AIRequest(prompt="Evaluate texture quality")
        >>> simple_response = backend.generate(simple_request)
        >>>
        >>> complex_request = AIRequest(
        ...     prompt="Plan comprehensive generation strategy..."
        ... )
        >>> complex_response = backend.generate(complex_request)
    """

    # Pricing (approximate - local model, but track equivalent cost)
    PRICING = {
        "unified-agent": {"input": 0.0, "output": 0.0},  # Local = free
    }

    def __init__(
        self,
        model: str = "TeichAI/gpt-oss-20b-claude-4.5-sonnet-high-reasoning-distill-GGUF",
        model_manager: Optional[ModelManager] = None,
        max_memory_gb: float = 16.0,  # Larger model (20B + distill)
        torch_dtype: torch.dtype = torch.float16,
        quantization: str = "Q8_0",  # GGUF quantization level
        keep_loaded: bool = True,  # Keep loaded (main model for 95% of calls)
        device: str = "cuda",
        **kwargs
    ):
        """
        Initialize unified agent backend.

        Args:
            model: Model identifier (TeichAI GGUF)
            model_manager: Shared ModelManager
            max_memory_gb: Max VRAM (larger model ~16GB)
            torch_dtype: Torch dtype
            quantization: GGUF quantization (Q8_0, Q6_K, Q4_K_M)
            keep_loaded: Keep model loaded (recommended - main model)
            device: Device to use
        """
        super().__init__(model=model)

        self.max_memory_gb = max_memory_gb
        self.torch_dtype = torch_dtype
        self.quantization = quantization
        self.keep_loaded = keep_loaded
        self.device = device

        # ModelManager integration
        self.model_manager = model_manager
        self._owns_manager = False

        self.model_name = "unified-agent"

    def initialize(self) -> None:
        """Initialize unified agent backend"""
        if self._initialized:
            return

        try:
            # Create ModelManager if not provided
            if self.model_manager is None:
                logger.info("Creating ModelManager for UnifiedAgent")
                self.model_manager = ModelManager(
                    max_total_memory_gb=self.max_memory_gb * 1.2,
                    auto_unload=not self.keep_loaded,
                )
                self._owns_manager = True

            # Register model with manager
            config = ModelConfig(
                name=self.model_name,
                role=ModelRole.PLANNER,  # Main agent (planner + executive)
                model_path=self.model,
                loader_func=self._create_loader(),
                max_memory_gb=self.max_memory_gb,
                priority=10,  # Highest priority (main model)
                keep_loaded=self.keep_loaded,
                torch_dtype=self.torch_dtype,
                device=self.device,
            )

            self.model_manager.register_model(config)

            # Pre-load if keep_loaded
            if self.keep_loaded:
                logger.info("Pre-loading UnifiedAgent (keep_loaded=True)")
                self.model_manager.load_model(self.model_name)

            self._initialized = True
            logger.info(f"UnifiedAgent initialized: {self.model}")
            logger.info("Handles: Executive function + Deep reasoning + Tool use")

        except Exception as e:
            raise AIError(f"Failed to initialize UnifiedAgent: {e}") from e

    def _create_loader(self):
        """Create loader function for unified agent"""
        def load_unified_agent(config: ModelConfig):
            # Note: GGUF models need llama-cpp-python (requires C++ build tools)
            # For now, we'll error gracefully if GGUF is used without llama-cpp

            # Check if it's a GGUF model
            if config.model_path.endswith('.gguf'):
                try:
                    from llama_cpp import Llama

                    logger.info(f"Loading UnifiedAgent with llama-cpp: {config.model_path}")

                    model = Llama(
                        model_path=config.model_path,
                        n_ctx=16384,
                        n_gpu_layers=-1,
                        n_threads=8,
                        n_batch=512,
                        verbose=False,
                    )

                    logger.info(f"UnifiedAgent loaded via llama-cpp")
                    return {"model": model, "backend": "llama-cpp"}

                except ImportError:
                    raise AIError(
                        "GGUF model requires llama-cpp-python. Install with:\n"
                        "pip install llama-cpp-python\n"
                        "Note: Requires C++ build tools on Windows."
                    )

            # Try transformers for non-GGUF models
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer

                logger.info(f"Loading UnifiedAgent with transformers: {config.model_path}")

                tokenizer = AutoTokenizer.from_pretrained(config.model_path)
                model = AutoModelForCausalLM.from_pretrained(
                    config.model_path,
                    torch_dtype=config.torch_dtype,
                    device_map="auto",
                    max_memory={0: f"{config.max_memory_gb}GB"},
                )

                return {
                    "model": model,
                    "tokenizer": tokenizer,
                    "backend": "transformers"
                }

            except Exception as e:
                raise AIError(f"Failed to load UnifiedAgent: {e}") from e

        return load_unified_agent

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using UnifiedAgent"""
        if not self._initialized:
            self.initialize()

        start_time = time.time()

        try:
            # Use model via context manager
            with self.model_manager.use_model(self.model_name) as model_dict:
                backend = model_dict.get("backend")

                if backend == "llama-cpp":
                    response_text = self._generate_llama_cpp(
                        model_dict["model"],
                        request
                    )
                    input_tokens = len(request.prompt.split()) * 1.3
                    output_tokens = len(response_text.split()) * 1.3

                elif backend == "transformers":
                    response_text, input_tokens, output_tokens = self._generate_transformers(
                        model_dict["model"],
                        model_dict["tokenizer"],
                        request
                    )

                else:
                    raise AIError(f"Unknown backend: {backend}")

                # Calculate stats
                total_tokens = int(input_tokens + output_tokens)
                latency_ms = (time.time() - start_time) * 1000

                # Cost (local = free)
                cost = 0.0

                # Update stats
                self._request_count += 1
                self._total_tokens += total_tokens
                self._total_cost += cost

                logger.debug(
                    f"UnifiedAgent generated ~{int(output_tokens)} tokens "
                    f"in {latency_ms:.0f}ms (free)"
                )

                return AIResponse(
                    content=response_text,
                    backend="unified-agent",
                    model=self.model,
                    tokens_used=total_tokens,
                    cost_estimate=cost,
                    latency_ms=latency_ms,
                    metadata={
                        "backend_type": backend,
                        "input_tokens": int(input_tokens),
                        "output_tokens": int(output_tokens),
                        "capabilities": "executive + planning + reasoning",
                    }
                )

        except Exception as e:
            logger.error(f"UnifiedAgent generation failed: {e}")
            raise AIError(f"Generation failed: {e}") from e

    def _generate_llama_cpp(
        self,
        model,
        request: AIRequest
    ) -> str:
        """Generate using llama-cpp-python"""
        # Build prompt with reasoning emphasis
        messages = []

        system_prompt = request.system_prompt or (
            "You are a highly capable AI assistant with advanced reasoning "
            "and planning abilities. You excel at both quick decisions and "
            "deep analysis."
        )

        messages.append({
            "role": "system",
            "content": system_prompt
        })

        messages.append({
            "role": "user",
            "content": request.prompt
        })

        # Generate
        response = model.create_chat_completion(
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            # Enhanced for reasoning
            repeat_penalty=1.1,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        return response["choices"][0]["message"]["content"]

    def _generate_transformers(
        self,
        model,
        tokenizer,
        request: AIRequest
    ) -> tuple[str, int, int]:
        """Generate using transformers"""
        # Build prompt
        messages = []

        system_prompt = request.system_prompt or (
            "You are a highly capable AI assistant with advanced reasoning "
            "and planning abilities."
        )

        messages.append({
            "role": "system",
            "content": system_prompt
        })

        messages.append({
            "role": "user",
            "content": request.prompt
        })

        # Format with chat template
        formatted_prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Tokenize
        inputs = tokenizer(
            formatted_prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=16384,  # Large context
        ).to(model.device)

        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                repetition_penalty=1.1,
            )

        # Decode
        input_tokens = inputs.input_ids.shape[1]
        generated_ids = outputs[0][input_tokens:]
        response_text = tokenizer.decode(
            generated_ids,
            skip_special_tokens=True
        )

        output_tokens = len(generated_ids)

        return response_text, input_tokens, output_tokens

    def is_available(self) -> bool:
        """Check if UnifiedAgent is available"""
        if not self._initialized:
            try:
                self.initialize()
                return True
            except:
                return False
        return True

    def shutdown(self) -> None:
        """Shutdown backend"""
        if self._owns_manager and self.model_manager:
            self.model_manager.shutdown()

        self._initialized = False
        logger.info("UnifiedAgent backend shutdown")

    def get_model_stats(self) -> Dict[str, Any]:
        """Get model-specific statistics"""
        base_stats = self.get_stats()

        if self.model_manager:
            model_status = self.model_manager.get_model_status(self.model_name)
            if model_status:
                base_stats["model_status"] = {
                    "state": model_status.state.value,
                    "memory_usage_gb": model_status.memory_usage_gb,
                    "load_count": model_status.load_count,
                    "last_used": model_status.last_used,
                }

            base_stats["manager_stats"] = self.model_manager.get_stats()

        base_stats["capabilities"] = [
            "executive_function",
            "deep_planning",
            "high_reasoning",
            "tool_use",
            "task_coordination",
        ]

        return base_stats
