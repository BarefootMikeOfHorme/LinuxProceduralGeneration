"""
VaultMind Forge - ControlNet Node Executors
Backend executors for ControlNet preprocessing and generation
"""

from typing import List, Dict, Any
from pathlib import Path
import uuid

from backend.core.base_executor import NodeExecutor, InputSpec, OutputSpec
from backend.core.types import DataType


class CannyPreprocessorExecutor(NodeExecutor):
    """Executor for Canny edge detection preprocessor node"""

    @property
    def node_type(self) -> str:
        return "cannyPreprocessor"

    @property
    def display_name(self) -> str:
        return "Canny Edge Detector"

    @property
    def category(self) -> str:
        return "controlnet"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec("image", DataType.IMAGE, required=True),
            InputSpec("low_threshold", DataType.NUMBER, required=False, default=100),
            InputSpec("high_threshold", DataType.NUMBER, required=False, default=200),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec("control_image", DataType.IMAGE),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Canny edge detection"""
        from PIL import Image
        from vaultmind_forge.forge_diffusion.controlnet_preprocessors import canny_edge_detection

        # Get inputs
        image_path = self.get_input_value(inputs, "image")
        low_threshold = int(self.get_input_value(inputs, "low_threshold", 100))
        high_threshold = int(self.get_input_value(inputs, "high_threshold", 200))

        print(f"[CannyPreprocessor] Processing image: {image_path}")
        print(f"[CannyPreprocessor] Thresholds: {low_threshold}-{high_threshold}")

        # Load image
        image = Image.open(image_path).convert("RGB")

        # Apply Canny edge detection
        control_image = canny_edge_detection(
            image,
            low_threshold=low_threshold,
            high_threshold=high_threshold
        )

        # Save control image
        output_dir = Path("outputs/controlnet")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"canny_{uuid.uuid4().hex[:8]}.png"
        control_image.save(output_path)

        print(f"[CannyPreprocessor] Saved control image: {output_path}")

        return {
            "control_image": str(output_path),
        }


class DepthPreprocessorExecutor(NodeExecutor):
    """Executor for depth estimation preprocessor node"""

    @property
    def node_type(self) -> str:
        return "depthPreprocessor"

    @property
    def display_name(self) -> str:
        return "Depth Map Estimator"

    @property
    def category(self) -> str:
        return "controlnet"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec("image", DataType.IMAGE, required=True),
            InputSpec("model", DataType.TEXT, required=False, default="midas"),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec("control_image", DataType.IMAGE),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute depth estimation"""
        from PIL import Image
        from vaultmind_forge.forge_diffusion.controlnet_preprocessors import depth_estimation

        # Get inputs
        image_path = self.get_input_value(inputs, "image")
        model = self.get_input_value(inputs, "model", "midas")

        print(f"[DepthPreprocessor] Processing image: {image_path}")
        print(f"[DepthPreprocessor] Model: {model}")

        # Load image
        image = Image.open(image_path).convert("RGB")

        # Estimate depth
        control_image, raw_depth = depth_estimation(image, model=model)

        # Save control image
        output_dir = Path("outputs/controlnet")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"depth_{uuid.uuid4().hex[:8]}.png"
        control_image.save(output_path)

        print(f"[DepthPreprocessor] Saved depth map: {output_path}")

        return {
            "control_image": str(output_path),
        }


class PosePreprocessorExecutor(NodeExecutor):
    """Executor for pose detection preprocessor node"""

    @property
    def node_type(self) -> str:
        return "posePreprocessor"

    @property
    def display_name(self) -> str:
        return "Pose Detector"

    @property
    def category(self) -> str:
        return "controlnet"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec("image", DataType.IMAGE, required=True),
            InputSpec("detect_hands", DataType.BOOLEAN, required=False, default=True),
            InputSpec("detect_face", DataType.BOOLEAN, required=False, default=True),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec("control_image", DataType.IMAGE),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pose detection"""
        from PIL import Image
        from vaultmind_forge.forge_diffusion.controlnet_preprocessors import pose_detection

        # Get inputs
        image_path = self.get_input_value(inputs, "image")
        detect_hands = bool(self.get_input_value(inputs, "detect_hands", True))
        detect_face = bool(self.get_input_value(inputs, "detect_face", True))

        print(f"[PosePreprocessor] Processing image: {image_path}")
        print(f"[PosePreprocessor] Detect hands: {detect_hands}, face: {detect_face}")

        # Load image
        image = Image.open(image_path).convert("RGB")

        # Detect pose
        control_image, pose_data = pose_detection(
            image,
            detect_hands=detect_hands,
            detect_face=detect_face
        )

        # Save control image
        output_dir = Path("outputs/controlnet")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"pose_{uuid.uuid4().hex[:8]}.png"
        control_image.save(output_path)

        print(f"[PosePreprocessor] Saved pose map: {output_path}")

        return {
            "control_image": str(output_path),
        }


class ControlNetLoaderExecutor(NodeExecutor):
    """Executor for ControlNet model loader node"""

    @property
    def node_type(self) -> str:
        return "controlnetLoader"

    @property
    def display_name(self) -> str:
        return "ControlNet Loader"

    @property
    def category(self) -> str:
        return "controlnet"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec("controlnet_type", DataType.TEXT, required=True),
            InputSpec("model_path", DataType.TEXT, required=False),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec("controlnet", DataType.MODEL),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load ControlNet model"""
        from vaultmind_forge.forge_diffusion.controlnet import ControlNetWrapper

        # Get inputs
        controlnet_type = self.get_input_value(inputs, "controlnet_type")
        model_path = self.get_input_value(inputs, "model_path", None)

        print(f"[ControlNetLoader] Loading {controlnet_type} ControlNet...")

        # Create wrapper and load model
        wrapper = ControlNetWrapper()
        wrapper.load_controlnet(controlnet_type, model_path=model_path)

        print(f"[ControlNetLoader] ControlNet loaded successfully")

        # Return the wrapper object (stored in cache)
        return {
            "controlnet": {
                "wrapper": wrapper,
                "type": controlnet_type,
            }
        }


class SDXLControlNetGeneratorExecutor(NodeExecutor):
    """Executor for SDXL generation with ControlNet guidance"""

    @property
    def node_type(self) -> str:
        return "sdxlControlNetGenerator"

    @property
    def display_name(self) -> str:
        return "SDXL ControlNet Generator"

    @property
    def category(self) -> str:
        return "generation"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec("prompt", DataType.TEXT, required=True),
            InputSpec("control_image", DataType.IMAGE, required=True),
            InputSpec("controlnet", DataType.MODEL, required=True),
            InputSpec("negative_prompt", DataType.TEXT, required=False, default=""),
            InputSpec("steps", DataType.NUMBER, required=False, default=30),
            InputSpec("cfg_scale", DataType.NUMBER, required=False, default=7.5),
            InputSpec("controlnet_scale", DataType.NUMBER, required=False, default=1.0),
            InputSpec("width", DataType.NUMBER, required=False, default=1024),
            InputSpec("height", DataType.NUMBER, required=False, default=1024),
            InputSpec("seed", DataType.NUMBER, required=False),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec("image", DataType.IMAGE),
            OutputSpec("metadata", DataType.DICT),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate image with ControlNet"""
        from PIL import Image
        import uuid

        # Get inputs
        prompt = self.get_input_value(inputs, "prompt")
        control_image_path = self.get_input_value(inputs, "control_image")
        controlnet_data = self.get_input_value(inputs, "controlnet")
        negative_prompt = self.get_input_value(inputs, "negative_prompt", "")
        steps = int(self.get_input_value(inputs, "steps", 30))
        cfg_scale = float(self.get_input_value(inputs, "cfg_scale", 7.5))
        controlnet_scale = float(self.get_input_value(inputs, "controlnet_scale", 1.0))
        width = int(self.get_input_value(inputs, "width", 1024))
        height = int(self.get_input_value(inputs, "height", 1024))
        seed = self.get_input_value(inputs, "seed", None)
        if seed is not None:
            seed = int(seed)

        print(f"[SDXLControlNetGenerator] Prompt: {prompt[:50]}...")
        print(f"[SDXLControlNetGenerator] ControlNet type: {controlnet_data['type']}")
        print(f"[SDXLControlNetGenerator] ControlNet scale: {controlnet_scale}")
        print(f"[SDXLControlNetGenerator] Steps: {steps}, CFG: {cfg_scale}")

        # Get ControlNet wrapper
        wrapper = controlnet_data["wrapper"]

        # Create pipeline if not already created
        if wrapper.pipeline is None:
            wrapper.create_pipeline()

        # Load control image
        control_image = Image.open(control_image_path).convert("RGB")

        # Generate
        result = wrapper.generate(
            prompt=prompt,
            control_image=control_image,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=cfg_scale,
            controlnet_conditioning_scale=controlnet_scale,
            width=width,
            height=height,
            seed=seed,
        )

        # Save generated image
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        image_path = output_dir / f"sdxl_controlnet_{uuid.uuid4().hex[:8]}.png"
        result["images"][0].save(image_path)

        print(f"[SDXLControlNetGenerator] Saved: {image_path}")

        return {
            "image": str(image_path),
            "metadata": result["metadata"],
        }
