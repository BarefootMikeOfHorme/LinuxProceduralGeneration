"""
Merlinv1 Backend - Local From-Scratch Language Model

Supports:
- Merlinv1 GPT-2 style model (42M params)
- Custom tokenizer (10K vocab)
- Zero pretrained bias
- Local inference (GPU/CPU)
- Built for Vaultmind Forge orchestration

Model trained from scratch on:
- Shakespeare
- Cornell Movie Dialogs
- LOTR
- Gutenberg samples
"""

from __future__ import annotations

import time
import logging
from typing import Optional
from pathlib import Path

from .base_ai import BaseAI, AIRequest, AIResponse, AIError

logger = logging.getLogger(__name__)


class Merlinv1Backend(BaseAI):
    """
    Merlinv1 local inference backend.

    Uses the from-scratch trained GPT-2 style model with custom tokenizer.

    Example:
        >>> backend = Merlinv1Backend(
        ...     model_path="C:/Merlinv1/checkpoints/final",
        ...     device="cuda"
        ... )
        >>> backend.initialize()
        >>> request = AIRequest(prompt="Generate a weapon description")
        >>> response = backend.generate(request)
    """

    def __init__(
        self,
        model_path: str = "C:/Merlinv1/checkpoints/final",
        device: str = "auto",
        **kwargs
    ):
        """
        Initialize Merlinv1 backend.

        Args:
            model_path: Path to trained Merlinv1 checkpoint
            device: Device to use (cuda, cpu, or auto)
        """
        super().__init__(model="merlinv1", api_key=None)
        self.model_path = Path(model_path)
        self.device = device
        self.tokenizer = None
        self.model = None
        self.actual_device = None

    def initialize(self) -> None:
        """Initialize Merlinv1 model and tokenizer"""
        if self._initialized:
            return

        try:
            from transformers import PreTrainedTokenizerFast, GPT2LMHeadModel
            import torch

            # Check model path exists
            if not self.model_path.exists():
                raise AIError(
                    f"Merlinv1 model not found at: {self.model_path}\n"
                    f"Run training first: cd C:/Merlinv1 && START_WITH_NEPTUNE.bat"
                )

            # Load tokenizer
            logger.info(f"Loading Merlinv1 tokenizer from: {self.model_path}")
            self.tokenizer = PreTrainedTokenizerFast.from_pretrained(str(self.model_path))

            # Load model
            logger.info(f"Loading Merlinv1 model from: {self.model_path}")
            self.model = GPT2LMHeadModel.from_pretrained(str(self.model_path))

            # Determine device
            if self.device == "auto":
                self.actual_device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                self.actual_device = self.device

            # Move model to device
            self.model.to(self.actual_device)
            self.model.eval()  # Set to evaluation mode

            # Log model info
            total_params = self.model.num_parameters()
            logger.info(
                f"Merlinv1 loaded: {total_params:,} params on {self.actual_device}"
            )

            self._initialized = True

        except ImportError as e:
            raise AIError(
                f"Required packages not installed: {e}\n"
                f"Install with: pip install transformers torch"
            ) from e
        except Exception as e:
            raise AIError(f"Failed to initialize Merlinv1: {e}") from e

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using Merlinv1"""
        if not self._initialized:
            self.initialize()

        import torch

        start_time = time.time()

        try:
            # Build prompt
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\n{request.prompt}"

            # Tokenize input
            inputs = self.tokenizer(
                full_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=4096  # Merlinv1 context window
            ).to(self.actual_device)

            input_length = inputs.input_ids.shape[1]

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=min(request.max_tokens, 4096 - input_length),
                    temperature=request.temperature,
                    top_p=request.top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )

            # Decode output
            generated_text = self.tokenizer.decode(
                outputs[0][input_length:],  # Skip input tokens
                skip_special_tokens=True
            )

            # Calculate stats
            latency_ms = (time.time() - start_time) * 1000
            output_tokens = outputs.shape[1] - input_length
            total_tokens = outputs.shape[1]

            # Local inference has no API cost
            cost = 0.0

            # Update stats
            self._request_count += 1
            self._total_tokens += total_tokens
            self._total_cost += cost

            logger.debug(
                f"Merlinv1 generated {output_tokens} tokens "
                f"in {latency_ms:.0f}ms on {self.actual_device}"
            )

            return AIResponse(
                content=generated_text,
                backend="merlinv1",
                model="merlinv1-42M",
                tokens_used=total_tokens,
                cost_estimate=cost,
                latency_ms=latency_ms,
                metadata={
                    "device": self.actual_device,
                    "input_tokens": input_length,
                    "output_tokens": output_tokens,
                }
            )

        except Exception as e:
            logger.error(f"Merlinv1 generation failed: {e}")
            raise AIError(f"Generation failed: {e}") from e

    def is_available(self) -> bool:
        """Check if Merlinv1 is available"""
        if not self._initialized:
            try:
                self.initialize()
                return True
            except:
                return False
        return True

    def shutdown(self) -> None:
        """Shutdown and free GPU memory"""
        if self.model is not None:
            del self.model
            self.model = None

        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None

        # Free CUDA memory if using GPU
        if self.actual_device == "cuda":
            try:
                import torch
                torch.cuda.empty_cache()
                logger.info("Merlinv1: CUDA memory freed")
            except:
                pass

        super().shutdown()
