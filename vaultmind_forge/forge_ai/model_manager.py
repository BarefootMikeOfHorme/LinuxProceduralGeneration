"""
Model Manager - Load/Eject Sequencer for Multi-Model AI System

Handles:
- Thread-safe model loading/unloading
- Memory management and optimization
- Model sequencing (planning model + helper models)
- GPU memory tracking
- Automatic model swapping based on task type

Strategy:
- Planning model (GPT-20B): Complex decisions, multi-step reasoning
- Helper models (smaller): Quick classifications, simple tasks
- Only one large model in memory at a time (memory efficient)
"""

from __future__ import annotations

import gc
import logging
import threading
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import torch

logger = logging.getLogger(__name__)


class ModelRole(str, Enum):
    """Model roles in the system"""
    PLANNER = "planner"           # Complex planning, multi-step reasoning (GPT-20B)
    HELPER = "helper"             # Quick tasks, classifications
    DIFFUSION = "diffusion"       # Image generation (FLUX, SDXL)


class ModelState(str, Enum):
    """Model loading states"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADING = "unloading"


@dataclass
class ModelConfig:
    """Configuration for a managed model"""
    name: str
    role: ModelRole
    model_path: str
    loader_func: Callable          # Function to load the model
    unloader_func: Optional[Callable] = None  # Custom unload logic
    max_memory_gb: float = 8.0     # Max VRAM usage
    priority: int = 1               # Higher = more important
    keep_loaded: bool = False       # Always keep in memory

    # Model-specific configs
    torch_dtype: torch.dtype = torch.float16
    device: str = "cuda"
    lora_weights: Optional[Dict[str, Any]] = None


@dataclass
class ModelStatus:
    """Current status of a model"""
    config: ModelConfig
    state: ModelState
    model_instance: Optional[Any] = None
    last_used: float = 0.0
    load_count: int = 0
    memory_usage_gb: float = 0.0


class ModelManager:
    """
    Thread-safe model manager with load/eject sequencer.

    Automatically loads and unloads models based on:
    - Memory constraints
    - Usage patterns
    - Task priorities

    Example:
        >>> manager = ModelManager(max_total_memory_gb=24.0)
        >>>
        >>> # Register planning model (GPT-20B)
        >>> manager.register_model(ModelConfig(
        ...     name="gpt-20b-planner",
        ...     role=ModelRole.PLANNER,
        ...     model_path="openai/gpt-oss-20b",
        ...     loader_func=load_gpt_20b,
        ...     max_memory_gb=12.0,
        ...     priority=10
        ... ))
        >>>
        >>> # Register diffusion model (FLUX)
        >>> manager.register_model(ModelConfig(
        ...     name="flux-diffusion",
        ...     role=ModelRole.DIFFUSION,
        ...     model_path="black-forest-labs/FLUX.1-dev",
        ...     loader_func=load_flux_model,
        ...     max_memory_gb=8.0,
        ...     lora_weights={"uncensored": "Heartsync/Flux-NSFW-uncensored"}
        ... ))
        >>>
        >>> # Use models - automatically handles loading/unloading
        >>> with manager.use_model("gpt-20b-planner") as planner:
        ...     result = planner.generate(prompt)
        >>>
        >>> with manager.use_model("flux-diffusion") as pipe:
        ...     image = pipe(prompt=prompt).images[0]
    """

    def __init__(
        self,
        max_total_memory_gb: float = 24.0,
        auto_unload: bool = True,
        unload_delay: float = 60.0,  # Seconds before unloading unused models
    ):
        """
        Initialize model manager.

        Args:
            max_total_memory_gb: Maximum total VRAM to use
            auto_unload: Automatically unload unused models
            unload_delay: Wait time before unloading (seconds)
        """
        self.max_total_memory_gb = max_total_memory_gb
        self.auto_unload = auto_unload
        self.unload_delay = unload_delay

        # Model registry
        self.models: Dict[str, ModelStatus] = {}

        # Thread safety
        self._lock = threading.RLock()
        self._model_locks: Dict[str, threading.RLock] = {}

        # Auto-unload thread
        self._unload_thread = None
        self._stop_unload_thread = False

        if auto_unload:
            self._start_unload_thread()

        logger.info(f"ModelManager initialized (max VRAM: {max_total_memory_gb}GB)")

    def register_model(self, config: ModelConfig) -> None:
        """Register a model for management"""
        with self._lock:
            if config.name in self.models:
                logger.warning(f"Model {config.name} already registered, updating config")

            self.models[config.name] = ModelStatus(
                config=config,
                state=ModelState.UNLOADED,
            )

            self._model_locks[config.name] = threading.RLock()

            logger.info(
                f"Registered model: {config.name} "
                f"(role={config.role.value}, max_memory={config.max_memory_gb}GB)"
            )

    def load_model(self, model_name: str) -> Any:
        """
        Load a model into memory.

        Automatically unloads other models if needed.

        Args:
            model_name: Name of model to load

        Returns:
            Loaded model instance
        """
        with self._lock:
            if model_name not in self.models:
                raise ValueError(f"Model {model_name} not registered")

            status = self.models[model_name]

            # Already loaded
            if status.state == ModelState.LOADED and status.model_instance is not None:
                status.last_used = time.time()
                logger.debug(f"Model {model_name} already loaded")
                return status.model_instance

            # Check if we need to free memory
            required_memory = status.config.max_memory_gb
            current_memory = self.get_total_memory_usage()

            if current_memory + required_memory > self.max_total_memory_gb:
                logger.info(
                    f"Need to free {required_memory}GB for {model_name} "
                    f"(current: {current_memory:.1f}GB, max: {self.max_total_memory_gb}GB)"
                )
                self._free_memory(required_memory)

        # Load model (outside main lock to avoid deadlock)
        with self._model_locks[model_name]:
            status = self.models[model_name]

            if status.state == ModelState.LOADED:
                return status.model_instance

            try:
                status.state = ModelState.LOADING
                logger.info(f"Loading model: {model_name}...")

                start_time = time.time()

                # Call loader function
                model_instance = status.config.loader_func(status.config)

                # Update status
                status.model_instance = model_instance
                status.state = ModelState.LOADED
                status.last_used = time.time()
                status.load_count += 1
                status.memory_usage_gb = self._estimate_model_memory(model_instance)

                load_time = time.time() - start_time

                logger.info(
                    f"Model {model_name} loaded in {load_time:.1f}s "
                    f"(memory: {status.memory_usage_gb:.1f}GB)"
                )

                return model_instance

            except Exception as e:
                status.state = ModelState.UNLOADED
                status.model_instance = None
                logger.error(f"Failed to load model {model_name}: {e}")
                raise

    def unload_model(self, model_name: str, force: bool = False) -> None:
        """
        Unload a model from memory.

        Args:
            model_name: Name of model to unload
            force: Force unload even if keep_loaded=True
        """
        with self._model_locks.get(model_name, threading.RLock()):
            if model_name not in self.models:
                return

            status = self.models[model_name]

            # Don't unload if keep_loaded (unless forced)
            if status.config.keep_loaded and not force:
                logger.debug(f"Model {model_name} marked keep_loaded, skipping unload")
                return

            if status.state != ModelState.LOADED:
                return

            try:
                status.state = ModelState.UNLOADING
                logger.info(f"Unloading model: {model_name}...")

                # Call custom unloader if provided
                if status.config.unloader_func:
                    status.config.unloader_func(status.model_instance)

                # Clear model
                status.model_instance = None
                status.memory_usage_gb = 0.0
                status.state = ModelState.UNLOADED

                # Cleanup GPU memory
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                gc.collect()

                logger.info(f"Model {model_name} unloaded")

            except Exception as e:
                logger.error(f"Error unloading model {model_name}: {e}")
                status.state = ModelState.UNLOADED

    def use_model(self, model_name: str):
        """
        Context manager for using a model.

        Automatically loads and tracks usage.

        Example:
            >>> with manager.use_model("gpt-20b-planner") as model:
            ...     result = model.generate(prompt)
        """
        return _ModelContext(self, model_name)

    def get_model_status(self, model_name: str) -> Optional[ModelStatus]:
        """Get current status of a model"""
        return self.models.get(model_name)

    def get_total_memory_usage(self) -> float:
        """Get total VRAM usage of all loaded models"""
        with self._lock:
            return sum(
                status.memory_usage_gb
                for status in self.models.values()
                if status.state == ModelState.LOADED
            )

    def get_loaded_models(self) -> list[str]:
        """Get list of currently loaded model names"""
        with self._lock:
            return [
                name
                for name, status in self.models.items()
                if status.state == ModelState.LOADED
            ]

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        with self._lock:
            return {
                "total_memory_usage_gb": self.get_total_memory_usage(),
                "max_memory_gb": self.max_total_memory_gb,
                "memory_utilization": self.get_total_memory_usage() / self.max_total_memory_gb,
                "loaded_models": self.get_loaded_models(),
                "model_stats": {
                    name: {
                        "state": status.state.value,
                        "memory_gb": status.memory_usage_gb,
                        "load_count": status.load_count,
                        "last_used": status.last_used,
                    }
                    for name, status in self.models.items()
                },
            }

    def shutdown(self) -> None:
        """Shutdown manager and unload all models"""
        logger.info("Shutting down ModelManager...")

        # Stop auto-unload thread
        self._stop_unload_thread = True
        if self._unload_thread:
            self._unload_thread.join(timeout=5.0)

        # Unload all models
        with self._lock:
            for model_name in list(self.models.keys()):
                self.unload_model(model_name, force=True)

        logger.info("ModelManager shutdown complete")

    def _free_memory(self, required_gb: float) -> None:
        """Free memory by unloading models"""
        with self._lock:
            # Get unloadable models (not keep_loaded, currently loaded)
            unloadable = [
                (name, status)
                for name, status in self.models.items()
                if status.state == ModelState.LOADED
                and not status.config.keep_loaded
            ]

            if not unloadable:
                logger.warning("No models available to unload!")
                return

            # Sort by priority (lower priority first) and last used time
            unloadable.sort(key=lambda x: (x[1].config.priority, -x[1].last_used))

            freed = 0.0
            for name, status in unloadable:
                if freed >= required_gb:
                    break

                logger.info(
                    f"Freeing memory by unloading {name} "
                    f"(priority={status.config.priority}, "
                    f"last_used={time.time() - status.last_used:.0f}s ago)"
                )

                self.unload_model(name)
                freed += status.memory_usage_gb

            logger.info(f"Freed {freed:.1f}GB of memory")

    def _estimate_model_memory(self, model_instance: Any) -> float:
        """Estimate model VRAM usage"""
        try:
            if torch.cuda.is_available():
                torch.cuda.synchronize()
                return torch.cuda.memory_allocated() / (1024 ** 3)
        except:
            pass

        # Fallback: estimate from model parameters
        try:
            if hasattr(model_instance, 'parameters'):
                params = sum(p.numel() for p in model_instance.parameters())
                # Assume float16 (2 bytes per param)
                return (params * 2) / (1024 ** 3)
        except:
            pass

        return 0.0

    def _start_unload_thread(self) -> None:
        """Start background thread for auto-unloading"""
        def unload_worker():
            while not self._stop_unload_thread:
                time.sleep(10)  # Check every 10 seconds

                current_time = time.time()

                with self._lock:
                    for name, status in list(self.models.items()):
                        if status.state != ModelState.LOADED:
                            continue

                        if status.config.keep_loaded:
                            continue

                        # Check if model is idle
                        idle_time = current_time - status.last_used
                        if idle_time >= self.unload_delay:
                            logger.info(
                                f"Auto-unloading {name} "
                                f"(idle for {idle_time:.0f}s)"
                            )
                            self.unload_model(name)

        self._unload_thread = threading.Thread(
            target=unload_worker,
            daemon=True,
            name="ModelManager-AutoUnload"
        )
        self._unload_thread.start()
        logger.info("Auto-unload thread started")


class _ModelContext:
    """Context manager for model usage"""

    def __init__(self, manager: ModelManager, model_name: str):
        self.manager = manager
        self.model_name = model_name
        self.model = None

    def __enter__(self):
        self.model = self.manager.load_model(self.model_name)
        return self.model

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Update last used time
        if self.model_name in self.manager.models:
            self.manager.models[self.model_name].last_used = time.time()


# Helper functions for common model types

def create_flux_loader(
    lora_weights: Optional[Dict[str, str]] = None
) -> Callable:
    """Create loader function for FLUX model"""
    def load_flux(config: ModelConfig):
        from diffusers import AutoPipelineForText2Image

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        logger.info(f"Loading FLUX model: {config.model_path}")
        pipe = AutoPipelineForText2Image.from_pretrained(
            config.model_path,
            torch_dtype=config.torch_dtype
        )
        pipe.to(device)

        # Load LoRA weights if provided
        if lora_weights or config.lora_weights:
            lora_config = lora_weights or config.lora_weights
            for adapter_name, lora_path in lora_config.items():
                logger.info(f"Loading LoRA: {adapter_name} from {lora_path}")
                pipe.load_lora_weights(
                    lora_path,
                    weight_name='lora.safetensors',
                    adapter_name=adapter_name
                )

        return pipe

    return load_flux


def create_gpt_loader() -> Callable:
    """Create loader function for GPT planning model"""
    def load_gpt(config: ModelConfig):
        from transformers import AutoModelForCausalLM, AutoTokenizer

        logger.info(f"Loading GPT model: {config.model_path}")

        tokenizer = AutoTokenizer.from_pretrained(config.model_path)
        model = AutoModelForCausalLM.from_pretrained(
            config.model_path,
            torch_dtype=config.torch_dtype,
            device_map="auto",  # Automatic device mapping
        )

        return {"model": model, "tokenizer": tokenizer}

    return load_gpt


def create_unloader() -> Callable:
    """Create generic unloader function"""
    def unload(model_instance):
        # Move to CPU if possible
        if hasattr(model_instance, 'to'):
            try:
                model_instance.to('cpu')
            except:
                pass

        # Delete references
        del model_instance

        # Cleanup
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    return unload
