from pathlib import Path
from dataclasses import dataclass
from typing import List
from pydantic import BaseModel
import random
import time

# Use backend manager if available
try:
    from .backends import get_backend_manager
except Exception:
    get_backend_manager = None

class ValidationResult(BaseModel):
    file: str
    score: float
    status: str
    checks: dict = {}

class Validator:
    def __init__(self):
        # config/thresholds could be loaded here
        self.threshold =0.5
        self._backend = get_backend_manager() if get_backend_manager is not None else None

    def validate_asset(self, path: Path | str) -> ValidationResult:
        """Run a fast mock validation: prefer native backend if available, otherwise random placeholder."""
        p = Path(path)
        if not p.exists():
            return ValidationResult(file=str(p), score=0.0, status="missing", checks={})

        if self._backend is not None:
            try:
                out = self._backend.validate_asset(p)
                # out may be dict-like; normalize
                if isinstance(out, dict):
                    return ValidationResult(**out)
                if hasattr(out, "model_dump"):
                    return ValidationResult(**out.model_dump())
                if hasattr(out, "dict"):
                    return ValidationResult(**out.dict())
                if hasattr(out, "__dict__"):
                    return ValidationResult(**out.__dict__)
                # fallback to manual mapping if sequence
                if isinstance(out, (list, tuple)):
                    if len(out) ==2:
                        score, status = out
                        return ValidationResult(file=str(p), score=float(score), status=str(status), checks={})
                    if len(out) >=3:
                        return ValidationResult(file=str(p), score=float(out[1]), status=str(out[2]), checks={})
            except Exception:
                # fallback to local behavior
                pass

        # placeholder checks (local fallback)
        score = round(random.uniform(0.3,1.0),3)
        status = "pass" if score >= self.threshold else "fail"
        checks = {"sharpness": round(random.uniform(0.3,1.0),3), "consistency": round(random.uniform(0.3,1.0),3)}
        return ValidationResult(file=str(p), score=score, status=status, checks=checks)
