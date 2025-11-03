from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
import logging
import importlib

logger = logging.getLogger("vaultmind_forge.diffusion")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# Minimal job model
class GenerationJob(BaseModel):
 name: str
 style: str
 target: tuple = (512,512)
 refs: list = []
 meta: dict = {}

# Placeholder simple generator (PNG placeholders)
def _placeholder_generate(job: GenerationJob, output_dir: Path, count: int =1) -> List[Path]:
 from PIL import Image
 output_dir = Path(output_dir)
 output_dir.mkdir(parents=True, exist_ok=True)
 paths = []
 for i in range(max(1, count)):
 p = output_dir / f"{job.name}_{i}.png"
 img = Image.new("RGBA", job.target, (100 + i*10,120 + i*5,200))
 img.save(p)
 paths.append(p)
 return paths

class DiffusersSDXLAdapter:
 """
 Adapter to Hugging Face diffusers (SDXL). Attempts to lazily import diffusers and torch.
 If libs or models aren't available, raise ImportError to let caller fallback.
 """

 def __init__(self, model_id: str = "stabilityai/stable-diffusion-xl-base-1.0", device: Optional[str]=None):
 self.model_id = model_id
 self.pipeline = None
 self.device = device
 self._available = None

 def _load(self):
 if self.pipeline is not None:
 return
 try:
 diffusers = importlib.import_module("diffusers")
 torch = importlib.import_module("torch")
 except ImportError as e:
 raise ImportError("diffusers or torch not installed") from e

 # Prefer CUDA if available and not explicitly forced off
 if self.device is None:
 self.device = "cuda" if torch.cuda.is_available() else "cpu"

 # Use the standard loading pattern; SDXL may use specialized pipelines
 from diffusers import DiffusionPipeline

 logger.info("Loading SDXL pipeline '%s' on device=%s", self.model_id, self.device)
 # Use safe kwargs (use_safetensors where available)
 # NOTE: user must have the model weights (or be logged in) for large models.
 pipe = DiffusionPipeline.from_pretrained(self.model_id, torch_dtype=None)
 pipe = pipe.to(self.device)
 self.pipeline = pipe

 def generate(self, job: GenerationJob, output_dir: Path, count: int =1, prompt: Optional[str] = None) -> List[Path]:
 self._load()
 output_dir = Path(output_dir)
 output_dir.mkdir(parents=True, exist_ok=True)
 results = []
 prompt = prompt or f"{job.style} {job.name}"
 for i in range(max(1, count)):
 # For SDXL we usually pass prompt and optionally negative prompt and guidance
 out = self.pipeline(prompt)[0] # returns images list; pipeline may also return dict
 # handle different return types
 if isinstance(out, list):
 img = out[0]
 elif hasattr(out, "images"):
 img = out.images[0]
 else:
 # Last resort: assume it's a PIL Image
 img = out
 p = output_dir / f"{job.name}_{i}.png"
 img.save(p)
 results.append(p)
 return results

class DiffusionGenerator:
 """Public generator: tries SDXL adapter, else fallback to placeholder generator."""

 def __init__(self, model_id: str = "stabilityai/stable-diffusion-xl-base-1.0", device: Optional[str] = None):
 self.model_id = model_id
 self.device = device
 # Attempt to create adapter lazily
 try:
 self.adapter = DiffusersSDXLAdapter(model_id=self.model_id, device=self.device)
 # attempt a quick availability probe by importing modules only
 importlib.import_module("diffusers")
 importlib.import_module("torch")
 self._use_adapter = True
 logger.info("Diffusers & torch available; SDXL adapter will be used when generating.")
 except Exception as e:
 logger.warning("Diffusers/Torch/SDXL not available or failed to init: %s; falling back to placeholder.", e)
 self.adapter = None
 self._use_adapter = False

 def generate(self, job: GenerationJob | dict, output_dir: Path | str, count: int =1, prompt: Optional[str] = None) -> List[Path]:
 if not isinstance(job, GenerationJob):
 job = GenerationJob(**job)
 if self._use_adapter and self.adapter is not None:
 try:
 return self.adapter.generate(job, Path(output_dir), count=count, prompt=prompt)
 except Exception as e:
 logger.exception("SDXL generation failed, falling back to placeholder: %s", e)
 return _placeholder_generate(job, Path(output_dir), count=count)
 else:
 return _placeholder_generate(job, Path(output_dir), count=count)
