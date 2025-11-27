"""
VaultMind Forge - ControlNet Wrapper
Spatial control for SDXL generation (edges, depth, pose)
"""

from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image
import torch

try:
    from diffusers import ControlNetModel, StableDiffusionXLControlNetPipeline
    from diffusers import AutoencoderKL
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False


class ControlNetWrapper:
    """
    Wrapper for ControlNet models with SDXL.

    Provides spatial control over generation using:
    - Canny edges
    - Depth maps
    - Pose keypoints
    """

    # HuggingFace model IDs for ControlNet models
    CONTROLNET_MODELS = {
        "canny": "diffusers/controlnet-canny-sdxl-1.0",
        "depth": "diffusers/controlnet-depth-sdxl-1.0",
        "openpose": "thibaud/controlnet-openpose-sdxl-1.0",
        "scribble": "xinsir/controlnet-scribble-sdxl-1.0",
        "normal": "diffusers/controlnet-normal-sdxl-1.0",
    }

    def __init__(self, device: str = "cuda", dtype: torch.dtype = torch.float16):
        """
        Initialize ControlNet wrapper.

        Args:
            device: Device to run on ("cuda" or "cpu")
            dtype: Data type for models (float16 or float32)
        """
        if not DIFFUSERS_AVAILABLE:
            raise ImportError("diffusers library not installed. Install with: pip install diffusers")

        self.device = device if torch.cuda.is_available() else "cpu"
        self.dtype = dtype if self.device == "cuda" else torch.float32

        self.controlnet = None
        self.controlnet_type = None
        self.pipeline = None

    def load_controlnet(self,
                        controlnet_type: str,
                        model_path: Optional[str] = None,
                        cache_dir: Optional[str] = None) -> None:
        """
        Load ControlNet model.

        Args:
            controlnet_type: Type of ControlNet (canny, depth, openpose, etc.)
            model_path: Optional custom model path (defaults to HuggingFace)
            cache_dir: Optional cache directory for models
        """
        # Get model ID from type or use custom path
        if model_path:
            model_id = model_path
        else:
            model_id = self.CONTROLNET_MODELS.get(controlnet_type.lower())
            if not model_id:
                raise ValueError(
                    f"Unknown ControlNet type: {controlnet_type}. "
                    f"Available types: {list(self.CONTROLNET_MODELS.keys())}"
                )

        print(f"[ControlNet] Loading {controlnet_type} model from {model_id}...")

        try:
            self.controlnet = ControlNetModel.from_pretrained(
                model_id,
                torch_dtype=self.dtype,
                cache_dir=cache_dir
            ).to(self.device)

            self.controlnet_type = controlnet_type
            print(f"[ControlNet] Model loaded successfully")

        except Exception as e:
            raise RuntimeError(f"Failed to load ControlNet model: {e}")

    def create_pipeline(self,
                       base_model_path: str = "stabilityai/stable-diffusion-xl-base-1.0",
                       vae_path: Optional[str] = None,
                       cache_dir: Optional[str] = None) -> StableDiffusionXLControlNetPipeline:
        """
        Create SDXL pipeline with ControlNet.

        Args:
            base_model_path: Path to SDXL base model
            vae_path: Optional custom VAE path
            cache_dir: Optional cache directory

        Returns:
            Configured StableDiffusionXLControlNetPipeline
        """
        if self.controlnet is None:
            raise ValueError("ControlNet not loaded. Call load_controlnet() first.")

        print(f"[ControlNet] Creating SDXL pipeline with {self.controlnet_type} control...")

        try:
            # Load custom VAE if specified
            vae = None
            if vae_path:
                vae = AutoencoderKL.from_pretrained(
                    vae_path,
                    torch_dtype=self.dtype
                ).to(self.device)

            # Create pipeline
            self.pipeline = StableDiffusionXLControlNetPipeline.from_pretrained(
                base_model_path,
                controlnet=self.controlnet,
                vae=vae,
                torch_dtype=self.dtype,
                cache_dir=cache_dir
            ).to(self.device)

            # Enable memory optimizations
            if self.device == "cuda":
                try:
                    self.pipeline.enable_xformers_memory_efficient_attention()
                    print("[ControlNet] xformers enabled")
                except Exception:
                    print("[ControlNet] xformers not available, using default attention")

            print("[ControlNet] Pipeline created successfully")
            return self.pipeline

        except Exception as e:
            raise RuntimeError(f"Failed to create pipeline: {e}")

    def generate(self,
                prompt: str,
                control_image: Image.Image,
                negative_prompt: str = "",
                num_inference_steps: int = 30,
                guidance_scale: float = 7.5,
                controlnet_conditioning_scale: float = 1.0,
                width: int = 1024,
                height: int = 1024,
                seed: Optional[int] = None,
                **kwargs) -> Dict[str, Any]:
        """
        Generate image with ControlNet guidance.

        Args:
            prompt: Text prompt
            control_image: Control image (edges, depth, pose, etc.)
            negative_prompt: Negative prompt
            num_inference_steps: Number of denoising steps
            guidance_scale: CFG scale
            controlnet_conditioning_scale: ControlNet strength (0.0-2.0)
            width: Output width
            height: Output height
            seed: Random seed (optional)
            **kwargs: Additional pipeline arguments

        Returns:
            Dict with generated images and metadata
        """
        if self.pipeline is None:
            raise ValueError("Pipeline not created. Call create_pipeline() first.")

        # Set seed if provided
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)

        # Resize control image to match output dimensions
        control_image_resized = control_image.resize((width, height), Image.Resampling.LANCZOS)

        print(f"[ControlNet] Generating with {self.controlnet_type} control (scale: {controlnet_conditioning_scale})...")

        try:
            result = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=control_image_resized,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                controlnet_conditioning_scale=controlnet_conditioning_scale,
                generator=generator,
                **kwargs
            )

            return {
                "images": result.images,
                "metadata": {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "controlnet_type": self.controlnet_type,
                    "controlnet_scale": controlnet_conditioning_scale,
                    "steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                    "width": width,
                    "height": height,
                    "seed": seed,
                }
            }

        except Exception as e:
            raise RuntimeError(f"Generation failed: {e}")

    def unload(self) -> None:
        """Unload models to free memory"""
        if self.pipeline:
            del self.pipeline
            self.pipeline = None
        if self.controlnet:
            del self.controlnet
            self.controlnet = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        print("[ControlNet] Models unloaded")


# Convenience function for quick usage
def generate_with_controlnet(
    prompt: str,
    control_image: Image.Image,
    controlnet_type: str = "canny",
    controlnet_scale: float = 1.0,
    steps: int = 30,
    width: int = 1024,
    height: int = 1024,
    **kwargs
) -> Image.Image:
    """
    Quick generation with ControlNet (loads models, generates, unloads).

    Args:
        prompt: Text prompt
        control_image: Control image
        controlnet_type: Type of control (canny, depth, openpose)
        controlnet_scale: ControlNet strength
        steps: Number of steps
        width: Output width
        height: Output height
        **kwargs: Additional arguments

    Returns:
        Generated image
    """
    wrapper = ControlNetWrapper()
    wrapper.load_controlnet(controlnet_type)
    wrapper.create_pipeline()

    result = wrapper.generate(
        prompt=prompt,
        control_image=control_image,
        num_inference_steps=steps,
        controlnet_conditioning_scale=controlnet_scale,
        width=width,
        height=height,
        **kwargs
    )

    wrapper.unload()

    return result["images"][0]


if __name__ == "__main__":
    # Test ControlNet wrapper
    print("ControlNet Wrapper - Test Mode")
    print(f"Available ControlNet types: {list(ControlNetWrapper.CONTROLNET_MODELS.keys())}")

    wrapper = ControlNetWrapper()
    print(f"Device: {wrapper.device}")
    print(f"Dtype: {wrapper.dtype}")
