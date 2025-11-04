from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple

PassName = Literal["base", "buildup", "refined"]

@dataclass
class MetricThresholds:
    min_sharpness: float = 0.55
    min_anatomy: float = 0.60
    min_prompt_alignment: float = 0.65
    min_consistency: float = 0.70
    min_color_fidelity: float = 0.65

@dataclass
class Evaluation:
    metrics: Dict[str, float]
    decision: Literal["accept", "retry", "reject"]
    remedies: List[Dict]

class Evaluator:
    def __init__(self, thresholds: MetricThresholds) -> None:
        self.thresholds = thresholds

    def evaluate(self, metrics: Dict[str, float]) -> Evaluation:
        remedies: List[Dict] = []
        decision = "accept"

        def below(v: float, min_v: float) -> bool:
            return v < min_v

        if below(metrics.get("sharpness", 0), self.thresholds.min_sharpness):
            decision = "retry"
            remedies.append({
                "issue": "Low sharpness",
                "prescription": "Increase CFG or denoise strength; apply mild USM; bump resolution + SR",
                "params": {"cfg_delta": +0.5, "denoise_delta": +0.05, "sr_model": "light"}
            })
        if below(metrics.get("anatomy", 0), self.thresholds.min_anatomy):
            decision = "retry"
            remedies.append({
                "issue": "Anatomy errors",
                "prescription": "Enable anatomy controlnet; stronger pose prior; guided inpaint on joints",
                "params": {"controlnet": "pose+openpose", "strength": 0.35, "mask": "joints"}
            })
        if below(metrics.get("prompt_alignment", 0), self.thresholds.min_prompt_alignment):
            decision = "retry"
            remedies.append({
                "issue": "Prompt misalignment",
                "prescription": "Boost key tokens; reduce style tokens; add negative terms",
                "params": {"token_weights": {"keywords": +0.2, "style": -0.1}, "negatives_add": ["blurry", "muted"]}
            })
        if below(metrics.get("consistency", 0), self.thresholds.min_consistency):
            decision = "retry"
            remedies.append({
                "issue": "Intra-sequence inconsistency",
                "prescription": "Lock seed & embeddings; raise IP-Adapter weight; freeze palette",
                "params": {"seed_lock": True, "ip_weight": +0.1, "palette_lock": True}
            })
        if below(metrics.get("color_fidelity", 0), self.thresholds.min_color_fidelity):
            decision = "retry"
            remedies.append({
                "issue": "Color drift",
                "prescription": "Enable palette enforcement; adjust white balance; clamp saturation",
                "params": {"palette": "reference", "wb": "auto+delta", "saturation_max": 0.85}
            })

        if not remedies:
            decision = "accept"
        return Evaluation(metrics=metrics, decision=decision, remedies=remedies)

class ThreePassRunner:
    def __init__(self, base: MetricThresholds, buildup: MetricThresholds, refined: MetricThresholds) -> None:
        self.passes: List[Tuple[PassName, MetricThresholds]] = [
            ("base", base),
            ("buildup", buildup),
            ("refined", refined),
        ]

    def run(self, metric_samples: Dict[PassName, Dict[str, float]]) -> List[Dict]:
        reports: List[Dict] = []
        for name, thresholds in self.passes:
            evaluator = Evaluator(thresholds)
            metrics = metric_samples.get(name, {})
            result = evaluator.evaluate(metrics)
            report = {
                "pass": name,
                "metrics": result.metrics,
                "thresholds": vars(thresholds),
                "decision": result.decision,
                "remedies": result.remedies,
            }
            reports.append(report)
        return reports