"""
GPT Planning Backend - openai/gpt-oss-20b

Specialized backend for complex planning and reasoning.
Uses ModelManager for efficient memory management.

Capabilities:
- Multi-step planning
- Complex reasoning
- Long context understanding
- Strategic decision making

Use for:
- Agent decision escalation
- Complex prompt refinement
- Multi-asset batch planning
- Quality assessment reasoning
"""

from __future__ import annotations

import time
import logging
from typing import Optional, Dict, Any

import torch

from .base_ai import BaseAI, AIRequest, AIResponse, AIError
from .model_manager import ModelManager, ModelConfig, ModelRole, create_gpt_loader

logger = logging.getLogger(__name__)


class GPTPlannerBackend(BaseAI):
    """
    GPT-20B planning backend with ModelManager integration.

    Example:
        >>> # Option 1: Use existing ModelManager
        >>> manager = ModelManager(max_total_memory_gb=24.0)
        >>> backend = GPTPlannerBackend(model_manager=manager)
        >>> backend.initialize()
        >>>
        >>> # Option 2: Create standalone (auto-creates manager)
        >>> backend = GPTPlannerBackend(model="openai/gpt-oss-20b")
        >>> backend.initialize()
        >>>
        >>> request = AIRequest(
        ...     prompt="Plan the generation strategy for a hero character texture",
        ...     system_prompt="You are an expert game asset planning AI"
        ... )
        >>> response = backend.generate(request)
    """

    # Pricing (approximate for OSS model - actual cost depends on hosting)
    PRICING = {
        "openai/gpt-oss-20b": {"input": 0.5, "output": 1.5},  # Per 1M tokens
    }

    def __init__(
        self,
        model: str = "openai/gpt-oss-20b",
        model_manager: Optional[ModelManager] = None,
        max_memory_gb: float = 12.0,
        torch_dtype: torch.dtype = torch.float16,
        keep_loaded: bool = False,  # Keep model in memory
        **kwargs
    ):
        """
        Initialize GPT planner backend.

        Args:
            model: Model identifier (openai/gpt-oss-20b)
            model_manager: Shared ModelManager (or create new one)
            max_memory_gb: Max VRAM for this model
            torch_dtype: Torch dtype (float16, bfloat16)
            keep_loaded: Always keep model loaded (for frequent use)
        """
        super().__init__(model=model)

        self.max_memory_gb = max_memory_gb
        self.torch_dtype = torch_dtype
        self.keep_loaded = keep_loaded

        # ModelManager integration
        self.model_manager = model_manager
        self._owns_manager = False  # Track if we created the manager

        self.model_name = "gpt-planner"

    def initialize(self) -> None:
        """Initialize GPT planner"""
        if self._initialized:
            return

        try:
            # Create ModelManager if not provided
            if self.model_manager is None:
                logger.info("Creating ModelManager for GPT planner")
                self.model_manager = ModelManager(
                    max_total_memory_gb=self.max_memory_gb * 1.5,  # Some headroom
                    auto_unload=not self.keep_loaded,
                )
                self._owns_manager = True

            # Register model with manager
            config = ModelConfig(
                name=self.model_name,
                role=ModelRole.PLANNER,
                model_path=self.model,
                loader_func=create_gpt_loader(),
                max_memory_gb=self.max_memory_gb,
                priority=10,  # High priority (planning is important)
                keep_loaded=self.keep_loaded,
                torch_dtype=self.torch_dtype,
            )

            self.model_manager.register_model(config)

            # Pre-load if keep_loaded
            if self.keep_loaded:
                logger.info("Pre-loading GPT planner (keep_loaded=True)")
                self.model_manager.load_model(self.model_name)

            self._initialized = True
            logger.info(f"GPT planner initialized: {self.model}")

        except Exception as e:
            raise AIError(f"Failed to initialize GPT planner: {e}") from e

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using GPT planner"""
        if not self._initialized:
            self.initialize()

        start_time = time.time()

        try:
            # Use model via context manager (auto-loads if needed)
            with self.model_manager.use_model(self.model_name) as model_dict:
                model = model_dict["model"]
                tokenizer = model_dict["tokenizer"]

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
                generated_ids = outputs[0][inputs.input_ids.shape[1]:]
                response_text = tokenizer.decode(
                    generated_ids,
                    skip_special_tokens=True
                )

                # Calculate stats
                input_tokens = inputs.input_ids.shape[1]
                output_tokens = len(generated_ids)
                total_tokens = input_tokens + output_tokens

                # Estimate cost
                pricing = self.PRICING.get(
                    self.model,
                    {"input": 0.5, "output": 1.5}
                )
                cost = (
                    (input_tokens / 1_000_000) * pricing["input"] +
                    (output_tokens / 1_000_000) * pricing["output"]
                )

                latency_ms = (time.time() - start_time) * 1000

                # Update stats
                self._request_count += 1
                self._total_tokens += total_tokens
                self._total_cost += cost

                logger.debug(
                    f"GPT planner generated {output_tokens} tokens "
                    f"in {latency_ms:.0f}ms (cost: ${cost:.4f})"
                )

                return AIResponse(
                    content=response_text,
                    backend="gpt-planner",
                    model=self.model,
                    tokens_used=total_tokens,
                    cost_estimate=cost,
                    latency_ms=latency_ms,
                    metadata={
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                    }
                )

        except Exception as e:
            logger.error(f"GPT planner generation failed: {e}")
            raise AIError(f"Generation failed: {e}") from e

    def is_available(self) -> bool:
        """Check if GPT planner is available"""
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
        logger.info("GPT planner backend shutdown")

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
