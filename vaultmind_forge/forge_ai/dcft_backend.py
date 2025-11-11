"""
DCFT Backend - oh-dcft-v3.1 (Claude 3.5 Haiku + Qwen)

Specialized backend for tool use and executive function.
This is a distilled model trained on Claude 3.5 Haiku and Qwen.

Use cases:
- Tool use and function calling
- Executive function and task coordination
- Structured output generation
- Agent decision making

Integration with multi-tier AI system:
- DCFT (this): Main executive function (80% of AI calls)
- GPT-20B: Deep planning and research (15% of AI calls)
- Helper (Ollama): Quick classifications (5% of AI calls)
"""

from __future__ import annotations

import time
import logging
from typing import Optional, Dict, Any

import torch

from .base_ai import BaseAI, AIRequest, AIResponse, AIError
from .model_manager import ModelManager, ModelConfig, ModelRole

logger = logging.getLogger(__name__)


class DCFTBackend(BaseAI):
    """
    DCFT backend for tool use and executive function.

    Optimized for:
    - Function calling and tool use
    - Structured output generation
    - Task coordination
    - Agent decision making

    Example:
        >>> # Option 1: Use existing ModelManager
        >>> manager = ModelManager(max_total_memory_gb=24.0)
        >>> backend = DCFTBackend(model_manager=manager)
        >>> backend.initialize()
        >>>
        >>> # Option 2: Create standalone
        >>> backend = DCFTBackend(
        ...     model="sizzlebop/oh-dcft-v3.1-claude-3-5-haiku-20241022-qwen-Q8_0-GGUF"
        ... )
        >>> backend.initialize()
        >>>
        >>> request = AIRequest(
        ...     prompt="Evaluate this texture quality and suggest improvements",
        ...     system_prompt="You are a game asset quality evaluator"
        ... )
        >>> response = backend.generate(request)
    """

    # Pricing (approximate - local model, but track equivalent cost)
    PRICING = {
        "oh-dcft": {"input": 0.0, "output": 0.0},  # Local = free
    }

    def __init__(
        self,
        model: str = "sizzlebop/oh-dcft-v3.1-claude-3-5-haiku-20241022-qwen-Q8_0-GGUF",
        model_manager: Optional[ModelManager] = None,
        max_memory_gb: float = 8.0,
        torch_dtype: torch.dtype = torch.float16,
        keep_loaded: bool = True,  # Keep loaded by default (main executive)
        device: str = "cuda",
        **kwargs
    ):
        """
        Initialize DCFT backend.

        Args:
            model: Model identifier (GGUF path or HF repo)
            model_manager: Shared ModelManager (or create new one)
            max_memory_gb: Max VRAM for this model
            torch_dtype: Torch dtype
            keep_loaded: Keep model loaded (recommended for executive function)
            device: Device to use (cuda/cpu)
        """
        super().__init__(model=model)

        self.max_memory_gb = max_memory_gb
        self.torch_dtype = torch_dtype
        self.keep_loaded = keep_loaded
        self.device = device

        # ModelManager integration
        self.model_manager = model_manager
        self._owns_manager = False

        self.model_name = "dcft-executive"

    def initialize(self) -> None:
        """Initialize DCFT backend"""
        if self._initialized:
            return

        try:
            # Create ModelManager if not provided
            if self.model_manager is None:
                logger.info("Creating ModelManager for DCFT")
                self.model_manager = ModelManager(
                    max_total_memory_gb=self.max_memory_gb * 1.5,
                    auto_unload=not self.keep_loaded,
                )
                self._owns_manager = True

            # Register model with manager
            config = ModelConfig(
                name=self.model_name,
                role=ModelRole.HELPER,  # Executive function role
                model_path=self.model,
                loader_func=self._create_loader(),
                max_memory_gb=self.max_memory_gb,
                priority=8,  # High priority (main executive)
                keep_loaded=self.keep_loaded,
                torch_dtype=self.torch_dtype,
                device=self.device,
            )

            self.model_manager.register_model(config)

            # Pre-load if keep_loaded
            if self.keep_loaded:
                logger.info("Pre-loading DCFT (keep_loaded=True)")
                self.model_manager.load_model(self.model_name)

            self._initialized = True
            logger.info(f"DCFT backend initialized: {self.model}")

        except Exception as e:
            raise AIError(f"Failed to initialize DCFT: {e}") from e

    def _create_loader(self):
        """Create loader function for DCFT model"""
        def load_dcft(config: ModelConfig):
            try:
                # Try llama-cpp-python for GGUF models
                from llama_cpp import Llama

                logger.info(f"Loading DCFT model with llama-cpp: {config.model_path}")

                model = Llama(
                    model_path=config.model_path,
                    n_ctx=8192,  # Context window
                    n_gpu_layers=-1,  # Use all GPU layers
                    n_threads=8,
                    verbose=False,
                )

                return {"model": model, "backend": "llama-cpp"}

            except ImportError:
                # Fallback to transformers
                try:
                    from transformers import AutoModelForCausalLM, AutoTokenizer

                    logger.info(f"Loading DCFT model with transformers: {config.model_path}")

                    tokenizer = AutoTokenizer.from_pretrained(config.model_path)
                    model = AutoModelForCausalLM.from_pretrained(
                        config.model_path,
                        torch_dtype=config.torch_dtype,
                        device_map="auto",
                    )

                    return {
                        "model": model,
                        "tokenizer": tokenizer,
                        "backend": "transformers"
                    }

                except Exception as e:
                    raise AIError(f"Failed to load DCFT model: {e}") from e

        return load_dcft

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using DCFT"""
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
                    f"DCFT generated ~{int(output_tokens)} tokens "
                    f"in {latency_ms:.0f}ms (free)"
                )

                return AIResponse(
                    content=response_text,
                    backend="dcft",
                    model=self.model,
                    tokens_used=total_tokens,
                    cost_estimate=cost,
                    latency_ms=latency_ms,
                    metadata={
                        "backend_type": backend,
                        "input_tokens": int(input_tokens),
                        "output_tokens": int(output_tokens),
                    }
                )

        except Exception as e:
            logger.error(f"DCFT generation failed: {e}")
            raise AIError(f"Generation failed: {e}") from e

    def _generate_llama_cpp(
        self,
        model,
        request: AIRequest
    ) -> str:
        """Generate using llama-cpp-python"""
        # Build prompt
        messages = []

        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
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

        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
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
        """Check if DCFT is available"""
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
        logger.info("DCFT backend shutdown")

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

        return base_stats
