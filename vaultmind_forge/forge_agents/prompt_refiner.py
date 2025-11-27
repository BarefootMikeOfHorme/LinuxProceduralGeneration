"""
Prompt Refiner Agent - Autonomous prompt enhancement

This agent autonomously improves prompts when generation fails,
using Merlinv1 AI model for intelligent refinement.

Capabilities:
- Analyzes failed generation metrics
- Uses Merlinv1 AI to enhance prompts
- Falls back to rule-based refinement if Merlinv1 unavailable
- Suggests style modifiers
- Emphasizes underrepresented concepts
- Learns from successful attempts
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import re
import logging

from .base_agent import (
    BaseAgent,
    AgentDecision,
    AgentCapability,
    EscalationReason,
)

logger = logging.getLogger(__name__)


@dataclass
class PromptRefinement:
    """Result of prompt refinement"""
    original_prompt: str
    refined_prompt: str
    refinements_added: List[str]
    confidence: float
    reasoning: str
    negative_prompt: Optional[str] = None


class PromptRefinerAgent(BaseAgent):
    """
    Autonomous prompt refinement agent.

    Analyzes generation failures and refines prompts to improve quality
    without requiring main AI consultation.
    """

    def __init__(
        self,
        min_confidence_threshold: float = 0.7,
        learning_enabled: bool = True,
        metrics_path: Optional[Path] = None,
        use_merlinv1: bool = True,
        merlinv1_path: Optional[str] = None,
    ):
        """
        Initialize Prompt Refiner Agent.

        Args:
            min_confidence_threshold: Minimum confidence to auto-apply refinements
            learning_enabled: Enable learning from successful refinements
            metrics_path: Path to save metrics
            use_merlinv1: Use Merlinv1 AI for prompt refinement (default True)
            merlinv1_path: Path to Merlinv1 model (default: C:/Merlinv1/checkpoints/final)
        """
        super().__init__(
            name="Prompt Refiner",
            capabilities=[AgentCapability.PROMPT_REFINEMENT],
        )

        # Set configuration
        self.confidence_threshold = min_confidence_threshold
        self.learning_enabled = learning_enabled
        self.metrics_path = metrics_path
        self.use_merlinv1 = use_merlinv1

        # Initialize Merlinv1 backend
        self.merlinv1_backend = None
        self.merlinv1_available = False

        if use_merlinv1:
            try:
                from vaultmind_forge.forge_ai.merlinv1_backend import Merlinv1Backend
                from vaultmind_forge.forge_ai.base_ai import AIRequest

                model_path = merlinv1_path or "C:/Merlinv1/checkpoints/final"
                self.merlinv1_backend = Merlinv1Backend(model_path=model_path)
                self.merlinv1_backend.initialize()
                self.merlinv1_available = True
                logger.info(f"[PromptRefiner] Merlinv1 backend loaded successfully")
            except Exception as e:
                logger.warning(f"[PromptRefiner] Merlinv1 unavailable, using rule-based refinement: {e}")
                self.merlinv1_available = False

        # Refinement patterns for different issues
        self.refinement_patterns = {
            # Quality issues
            "low_sharpness": [
                "highly detailed",
                "sharp focus",
                "8k uhd",
                "high quality",
                "crisp details",
            ],
            "low_contrast": [
                "high contrast",
                "dramatic lighting",
                "professional photography",
            ],
            "desaturated": [
                "vibrant colors",
                "rich colors",
                "saturated",
            ],
            "blurry": [
                "sharp",
                "in focus",
                "detailed",
                "high resolution",
            ],

            # Anatomy issues (for characters)
            "anatomy_problems": [
                "correct proportions",
                "professional anatomy",
                "anatomically correct",
                "well-proportioned",
            ],

            # Prompt alignment issues
            "weak_alignment": [
                "masterpiece",
                "best quality",
                "highly detailed",
            ],

            # Style issues
            "style_mismatch": {
                "photorealistic": ["photorealistic", "8k", "ray tracing", "unreal engine"],
                "anime": ["anime", "high quality anime", "clean lines", "vibrant colors"],
                "game_art": ["game art", "stylized", "fantasy art", "concept art"],
            },
        }

        # Common negative prompt additions
        self.negative_prompt_additions = {
            "quality": ["blurry", "low quality", "worst quality", "low resolution"],
            "artifacts": ["artifacts", "jpeg artifacts", "noise", "grain"],
            "anatomy": ["bad anatomy", "bad proportions", "deformed", "mutated"],
            "composition": ["bad composition", "poorly drawn", "amateur"],
        }

        # Track successful refinements
        self.successful_refinements: Dict[str, List[str]] = {}

    def _refine_with_merlinv1(
        self,
        original_prompt: str,
        style: Optional[str] = None,
        failed_metrics: Optional[Dict[str, float]] = None,
    ) -> Optional[str]:
        """
        Use Merlinv1 AI to refine prompt.

        Args:
            original_prompt: Original prompt text
            style: Desired style
            failed_metrics: Quality metrics from failed generation

        Returns:
            Refined prompt or None if Merlinv1 unavailable
        """
        if not self.merlinv1_available or not self.merlinv1_backend:
            return None

        try:
            from vaultmind_forge.forge_ai.base_ai import AIRequest

            # Build context for Merlinv1
            system_prompt = (
                "You are an expert prompt engineer for AI image generation. "
                "Enhance the following prompt to produce higher quality outputs. "
                "Add specific details, quality modifiers, and style keywords. "
                "Keep the core concept intact. Output only the enhanced prompt."
            )

            # Add style context if provided
            if style:
                system_prompt += f"\nTarget style: {style}"

            # Add failure context if we have metrics
            if failed_metrics:
                issues = []
                if failed_metrics.get("sharpness", 1.0) < 0.7:
                    issues.append("low sharpness")
                if failed_metrics.get("contrast", 1.0) < 0.6:
                    issues.append("low contrast")
                if failed_metrics.get("saturation", 1.0) < 0.5:
                    issues.append("desaturated colors")

                if issues:
                    system_prompt += f"\nPrevious generation had: {', '.join(issues)}"

            # Create AI request
            request = AIRequest(
                prompt=f"Original prompt: {original_prompt}\n\nEnhanced prompt:",
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=150,
                top_p=0.9,
            )

            # Generate refinement
            response = self.merlinv1_backend.generate(request)
            refined = response.content.strip()

            # Clean up the response
            # Remove quotes if Merlinv1 added them
            refined = refined.strip('"\'')

            # If Merlinv1 returned something reasonable, use it
            if refined and len(refined) > len(original_prompt) * 0.5:
                logger.info(f"[PromptRefiner] Merlinv1 refined: {original_prompt[:50]}... -> {refined[:50]}...")
                return refined
            else:
                logger.warning(f"[PromptRefiner] Merlinv1 output too short, falling back to rules")
                return None

        except Exception as e:
            logger.error(f"[PromptRefiner] Merlinv1 refinement failed: {e}")
            return None

    def refine_prompt(
        self,
        original_prompt: str,
        failed_metrics: Optional[Dict[str, float]] = None,
        attempt_history: Optional[List[Dict[str, Any]]] = None,
        style: Optional[str] = None,
    ) -> PromptRefinement:
        """
        Refine a prompt based on failure analysis.

        Uses Merlinv1 AI for intelligent refinement when available,
        falls back to rule-based refinement otherwise.

        Args:
            original_prompt: Original generation prompt
            failed_metrics: Quality metrics from failed generation
            attempt_history: History of previous attempts
            style: Detected or specified style

        Returns:
            PromptRefinement with refined prompt and confidence
        """
        # Try Merlinv1 AI-powered refinement first
        merlinv1_refined = self._refine_with_merlinv1(
            original_prompt,
            style=style,
            failed_metrics=failed_metrics
        )

        if merlinv1_refined:
            # Merlinv1 succeeded - use AI-generated refinement
            reasoning = "Refined using Merlinv1 AI"
            if style:
                reasoning += f" ({style} style)"
            if failed_metrics:
                issues = [k for k, v in failed_metrics.items() if isinstance(v, (int, float)) and v < 0.7]
                if issues:
                    reasoning += f"; addressed: {', '.join(issues)}"

            # Calculate confidence (higher for AI refinement)
            confidence = 0.85  # High confidence in Merlinv1

            # Track decision
            decision = AgentDecision(
                action="REFINE",
                confidence=confidence,
                reasoning=reasoning,
                metadata={
                    "original_prompt": original_prompt,
                    "refined_prompt": merlinv1_refined,
                    "method": "merlinv1_ai",
                    "style": style,
                }
            )
            self.record_decision(decision)

            return PromptRefinement(
                original_prompt=original_prompt,
                refined_prompt=merlinv1_refined,
                refinements_added=["AI-enhanced"],
                confidence=confidence,
                reasoning=reasoning,
                negative_prompt=self._build_negative_prompt(failed_metrics),
            )

        # Fallback to rule-based refinement
        logger.info("[PromptRefiner] Using rule-based refinement")
        refinements = []
        reasoning_parts = ["Using rule-based refinement"]

        # Analyze metrics and add appropriate refinements
        if failed_metrics:
            # Low sharpness
            if failed_metrics.get("sharpness", 1.0) < 0.7:
                refinements.extend(self.refinement_patterns["low_sharpness"][:2])
                reasoning_parts.append("Added sharpness keywords (low sharpness detected)")

            # Low contrast
            if failed_metrics.get("contrast", 1.0) < 0.6:
                refinements.extend(self.refinement_patterns["low_contrast"][:1])
                reasoning_parts.append("Added contrast keywords")

            # Desaturated
            if failed_metrics.get("saturation", 1.0) < 0.5:
                refinements.extend(self.refinement_patterns["desaturated"][:1])
                reasoning_parts.append("Added color saturation keywords")

            # Anatomy issues (if character/person detected)
            if "character" in original_prompt.lower() or "person" in original_prompt.lower():
                if failed_metrics.get("anatomy", 1.0) < 0.6:
                    refinements.extend(self.refinement_patterns["anatomy_problems"][:2])
                    reasoning_parts.append("Added anatomy correction keywords")

            # Weak prompt alignment
            if failed_metrics.get("prompt_alignment", 1.0) < 0.75:
                # Emphasize key concepts
                key_concepts = self._extract_key_concepts(original_prompt)
                if key_concepts:
                    # Add emphasis to first key concept
                    refinements.append(f"({key_concepts[0]}:1.2)")
                    reasoning_parts.append(f"Emphasized key concept: {key_concepts[0]}")

        # Add style-specific refinements
        if style and style in self.refinement_patterns["style_mismatch"]:
            style_keywords = self.refinement_patterns["style_mismatch"][style]
            # Only add if not already in prompt
            for keyword in style_keywords[:2]:
                if keyword.lower() not in original_prompt.lower():
                    refinements.append(keyword)
            if any(kw not in original_prompt.lower() for kw in style_keywords[:2]):
                reasoning_parts.append(f"Added {style} style keywords")

        # Learn from attempt history
        if attempt_history and self.learning_enabled:
            successful_patterns = self._find_successful_patterns(attempt_history)
            refinements.extend(successful_patterns[:2])
            if successful_patterns:
                reasoning_parts.append("Applied learned successful patterns")

        # If no specific refinements, add general quality boost
        if not refinements:
            refinements = ["highly detailed", "best quality"]
            reasoning_parts.append("Added general quality boost")

        # Build refined prompt
        # Remove duplicates while preserving order
        unique_refinements = []
        seen = set()
        for ref in refinements:
            ref_lower = ref.lower()
            if ref_lower not in seen and ref_lower not in original_prompt.lower():
                unique_refinements.append(ref)
                seen.add(ref_lower)

        refined_prompt = f"{original_prompt}, {', '.join(unique_refinements)}"

        # Build negative prompt
        negative_prompt = self._build_negative_prompt(failed_metrics)

        # Calculate confidence
        confidence = self._calculate_refinement_confidence(
            original_prompt,
            unique_refinements,
            failed_metrics,
            attempt_history,
        )

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "General enhancement"

        # Track decision
        decision = AgentDecision(
            action="REFINE",
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                "original_prompt": original_prompt,
                "refined_prompt": refined_prompt,
                "refinements": unique_refinements,
                "style": style,
            }
        )
        self.record_decision(decision)

        return PromptRefinement(
            original_prompt=original_prompt,
            refined_prompt=refined_prompt,
            refinements_added=unique_refinements,
            confidence=confidence,
            reasoning=reasoning,
            negative_prompt=negative_prompt,
        )

    def _extract_key_concepts(self, prompt: str) -> List[str]:
        """Extract key nouns/concepts from prompt"""
        # Simple keyword extraction (could be enhanced with NLP)
        # Remove common words
        common_words = {"a", "an", "the", "of", "in", "on", "at", "to", "for", "with"}

        words = re.findall(r'\w+', prompt.lower())
        key_words = [w for w in words if w not in common_words and len(w) > 3]

        # Return first 3 most important words (simple heuristic: longer = more specific)
        return sorted(key_words, key=len, reverse=True)[:3]

    def _find_successful_patterns(
        self,
        attempt_history: List[Dict[str, Any]]
    ) -> List[str]:
        """Find patterns from successful attempts"""
        successful_keywords = []

        for attempt in attempt_history:
            if attempt.get("success", False) and attempt.get("quality_score", 0) > 0.75:
                prompt = attempt.get("prompt", "")
                # Extract keywords that weren't in original
                # (This is simplified - could track diff between prompts)
                if "highly detailed" in prompt.lower():
                    successful_keywords.append("highly detailed")
                if "masterpiece" in prompt.lower():
                    successful_keywords.append("masterpiece")

        return list(set(successful_keywords))[:3]

    def _build_negative_prompt(
        self,
        failed_metrics: Optional[Dict[str, float]]
    ) -> str:
        """Build negative prompt based on failures"""
        negative_parts = []

        # Always add quality negatives
        negative_parts.extend(self.negative_prompt_additions["quality"][:2])

        # Add specific negatives based on metrics
        if failed_metrics:
            if failed_metrics.get("anatomy", 1.0) < 0.6:
                negative_parts.extend(self.negative_prompt_additions["anatomy"][:2])

            if failed_metrics.get("sharpness", 1.0) < 0.5:
                negative_parts.extend(["blurry", "out of focus"])

        return ", ".join(list(set(negative_parts)))

    def _calculate_refinement_confidence(
        self,
        original_prompt: str,
        refinements: List[str],
        failed_metrics: Optional[Dict[str, float]],
        attempt_history: Optional[List[Dict[str, Any]]],
    ) -> float:
        """Calculate confidence in refinement"""
        confidence = 0.5  # Base confidence

        # More refinements = more confidence (up to a point)
        confidence += min(len(refinements) * 0.1, 0.3)

        # If we have clear metrics indicating what's wrong, higher confidence
        if failed_metrics:
            # Count how many metrics are below threshold
            issues_detected = sum(
                1 for v in failed_metrics.values()
                if isinstance(v, (int, float)) and v < 0.7
            )
            confidence += min(issues_detected * 0.05, 0.15)

        # If we have attempt history, slight boost
        if attempt_history:
            confidence += 0.05

        # If original prompt is very short, lower confidence (too vague)
        if len(original_prompt.split()) < 3:
            confidence -= 0.1

        return min(max(confidence, 0.0), 1.0)

    def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """
        Make decision (required by BaseAgent).
        For Prompt Refiner, the decision is made in refine_prompt().
        """
        # Extract context
        original_prompt = context.get("original_prompt", "")
        failed_metrics = context.get("failed_metrics")
        style = context.get("style")

        # Refine
        refinement = self.refine_prompt(
            original_prompt,
            failed_metrics=failed_metrics,
            style=style,
        )

        # Return decision
        return AgentDecision(
            action="REFINE" if refinement.confidence >= self.confidence_threshold else "ESCALATE",
            confidence=refinement.confidence,
            reasoning=refinement.reasoning,
            metadata={
                "refined_prompt": refinement.refined_prompt,
                "refinements": refinement.refinements_added,
            },
            escalation_reason=EscalationReason.LOW_CONFIDENCE if refinement.confidence < self.confidence_threshold else None,
        )

    def calculate_confidence(
        self,
        context: Dict[str, Any],
        proposed_action: str
    ) -> float:
        """Calculate confidence for proposed action"""
        return self._calculate_refinement_confidence(
            original_prompt=context.get("original_prompt", ""),
            refinements=context.get("refinements", []),
            failed_metrics=context.get("failed_metrics"),
            attempt_history=context.get("attempt_history"),
        )
