from dataclasses import dataclass
from typing import Tuple

@dataclass
class GenerationJob:
    name: str
    style: str
    target: Tuple[int,int]
    refs: list = None
    meta: dict = None

class Planner:
    def plan_simple_job(self, name: str, style: str = "photoreal", target=(512,512)) -> GenerationJob:
        """Return a minimal job description used by generator stubs."""
        return GenerationJob(name=name, style=style, target=target, refs=[], meta={})
