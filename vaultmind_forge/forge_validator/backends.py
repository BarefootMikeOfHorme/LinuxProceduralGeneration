"""
Backend loader for forge_validator.

Behavior:
 - Attempt to import the native Rust extension (built via maturin).
 - If present, use it as the primary validator backend.
 - Otherwise use the pure-Python Validator as fallback.
 - Exposes a uniform BackendManager with validate_asset(...) API.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import importlib
import logging

logger = logging.getLogger("vaultmind_forge.validator.backends")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# Local python validator fallback
try:
 # Import local pure-Python validator
 from .validator import Validator as PurePythonValidator # relative import
except Exception as e:
 PurePythonValidator = None
 logger.debug("Pure-Python Validator not importable: %s", e)


class RustBackendWrapper:
 """Wrap a native Rust-produced Python extension (PyO3) to present a uniform API."""

 def __init__(self, module: Any):
 self.module = module
 # Try to detect available functions
 # Expectation: module exposes `validate_image(path: str) -> dict` or similar.
 # This is flexible — adapt to your Rust API shape later.
 logger.info("Using Rust backend module: %s", getattr(module, "__name__", "<rust>"))

 def validate_asset(self, path: Path) -> Dict:
 """Call into Rust module and normalize result into dict with keys (file,score,status,checks)."""
 p = str(path)
 # Common patterns:
 #1) module.validate_image(path) returning dict-like
 #2) module.validate(path) -> tuple or simple primitives
 if hasattr(self.module, "validate_image"):
 out = self.module.validate_image(p)
 elif hasattr(self.module, "validate"):
 out = self.module.validate(p)
 else:
 raise RuntimeError("Rust module does not expose validate_image or validate")
 # Normalize into our ValidationResult-shaped dict
 if isinstance(out, dict):
 return out
 # If out is tuple/list, try to map it
 if isinstance(out, (list, tuple)):
 # try to be forgiving: (score, status) or (file, score, status)
 if len(out) ==2:
 score, status = out
 return {"file": p, "score": float(score), "status": str(status), "checks": {}}
 elif len(out) >=3:
 return {"file": p, "score": float(out[1]), "status": str(out[2]), "checks": {}}
 # fallback
 return {"file": p, "score":0.0, "status": "unknown", "checks": {}}


class PurePythonWrapper:
 """Wrap the pure-Python Validator class to the same API surface as RustBackendWrapper."""

 def __init__(self):
 if PurePythonValidator is None:
 raise RuntimeError("No pure-Python validator available")
 self._impl = PurePythonValidator()
 logger.info("Using Pure-Python Validator backend")

 def validate_asset(self, path: Path) -> Dict:
 r = self._impl.validate_asset(path)
 # If the pure validator returns a Pydantic model, convert to dict
 if hasattr(r, "model_dump"): # pydantic v2
 return r.model_dump()
 if hasattr(r, "dict"): # pydantic v1
 return r.dict()
 # dataclass fallback
 if hasattr(r, "__dict__"):
 return r.__dict__
 # if already a dict-like
 return dict(r)


class BackendManager:
 """
 Manager that picks the best available backend:
1) Attempts to import a Rust/maturin-built extension (common name guessed 'vmf_validator' per docs)
2) Falls back to the pure-Python validator
 """

 def __init__(self, rust_module_name: str | None = None):
 self.rust_module_name = rust_module_name or "vmf_validator"
 self.backend = self._detect_backend()

 def _detect_backend(self):
 #1) Try to import the rust module by name
 try:
 mod = importlib.import_module(self.rust_module_name)
 logger.info("Imported native validator module: %s", self.rust_module_name)
 return RustBackendWrapper(mod)
 except Exception as e:
 logger.info("Native validator import failed: %s", e)

 #2) Fallback to local pure python wrapper
 try:
 return PurePythonWrapper()
 except Exception as e:
 logger.error("No validator backend available: %s", e)
 raise RuntimeError("No validator backend available") from e

 def validate_asset(self, path: Path) -> Dict:
 return self.backend.validate_asset(Path(path))


# convenience singleton
_backend_manager: Optional[BackendManager] = None


def get_backend_manager() -> BackendManager:
 global _backend_manager
 if _backend_manager is None:
 _backend_manager = BackendManager()
 return _backend_manager
