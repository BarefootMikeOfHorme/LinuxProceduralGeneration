"""
VaultMind Forge - Job Planner
Intelligent job planning and helper pass selection
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import uuid

from .schemas import (
    JobConfig,
    OutputType,
    RenderStyle,
    QualityPreset,
    StyleConstraints,
    ValidationRequirements,
    GenerationParams,
    AspectRatio,
    LineageConfig,
    Reference,
)


class HelperPass(str, Enum):
    """Available helper passes for generation control"""
    DEPTH_MAP = "depth_map"
    CANNY_EDGE = "canny_edge"
    POSE_SKELETON = "pose_skeleton"
    SEGMENTATION = "segmentation"
    NORMAL_MAP = "normal_map"
    LINE_ART = "line_art"
    SCRIBBLE = "scribble"
    COLOR_PALETTE = "color_palette"
    IP_ADAPTER = "ip_adapter"


@dataclass
class GenerationPlan:
    """
    Complete generation plan with recommended helper passes and parameters.
    """
    job_config: JobConfig
    recommended_helpers: List[HelperPass]
    estimated_time_minutes: float
    estimated_memory_gb: float
    optimization_notes: List[str]
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_config": self.job_config.to_dict(),
            "recommended_helpers": [h.value for h in self.recommended_helpers],
            "estimated_time_minutes": self.estimated_time_minutes,
            "estimated_memory_gb": self.estimated_memory_gb,
            "optimization_notes": self.optimization_notes,
            "warnings": self.warnings,
        }


class JobPlanner:
    """
    Intelligent job planner that analyzes requirements and generates
    optimized generation plans.

    Features:
    - Automatic helper pass selection based on output type
    - Resource estimation (time, memory)
    - Parameter optimization
    - Validation requirement analysis
    - Multi-pass strategy planning
    """

    # Helper pass recommendations by output type
    HELPER_RECOMMENDATIONS = {
        OutputType.CHARACTER_2D: [
            HelperPass.POSE_SKELETON,
            HelperPass.CANNY_EDGE,
            HelperPass.COLOR_PALETTE,
        ],
        OutputType.CHARACTER_3D: [
            HelperPass.DEPTH_MAP,
            HelperPass.NORMAL_MAP,
            HelperPass.POSE_SKELETON,
        ],
        OutputType.ENVIRONMENT: [
            HelperPass.DEPTH_MAP,
            HelperPass.SEGMENTATION,
            HelperPass.LINE_ART,
        ],
        OutputType.CONCEPT_ART: [
            HelperPass.SCRIBBLE,
            HelperPass.COLOR_PALETTE,
            HelperPass.LINE_ART,
        ],
        OutputType.TECHNICAL_DIAGRAM: [
            HelperPass.CANNY_EDGE,
            HelperPass.LINE_ART,
            HelperPass.SEGMENTATION,
        ],
        OutputType.STORYBOARD: [
            HelperPass.SCRIBBLE,
            HelperPass.LINE_ART,
        ],
    }

    # Base time estimates (minutes) by quality preset
    BASE_TIME_ESTIMATES = {
        QualityPreset.DRAFT: 0.5,
        QualityPreset.STANDARD: 1.5,
        QualityPreset.HIGH: 3.0,
        QualityPreset.PRODUCTION: 6.0,
    }

    # Base memory estimates (GB) by quality preset
    BASE_MEMORY_ESTIMATES = {
        QualityPreset.DRAFT: 4.0,
        QualityPreset.STANDARD: 6.0,
        QualityPreset.HIGH: 8.0,
        QualityPreset.PRODUCTION: 12.0,
    }

    def __init__(self):
        """Initialize job planner"""
        self.plans_created = 0

    def create_plan(self, job_config: JobConfig) -> GenerationPlan:
        """
        Create a complete generation plan from job configuration.

        Args:
            job_config: Job configuration

        Returns:
            GenerationPlan with recommendations and estimates
        """
        self.plans_created += 1

        # Determine recommended helper passes
        helpers = self._recommend_helpers(job_config)

        # Estimate resource requirements
        time_estimate = self._estimate_time(job_config, helpers)
        memory_estimate = self._estimate_memory(job_config, helpers)

        # Generate optimization notes
        optimization_notes = self._generate_optimization_notes(job_config)

        # Check for warnings
        warnings = self._check_warnings(job_config)

        return GenerationPlan(
            job_config=job_config,
            recommended_helpers=helpers,
            estimated_time_minutes=time_estimate,
            estimated_memory_gb=memory_estimate,
            optimization_notes=optimization_notes,
            warnings=warnings,
        )

    def _recommend_helpers(self, job_config: JobConfig) -> List[HelperPass]:
        """Recommend helper passes based on job configuration"""
        helpers = []

        # Base recommendations by output type
        if job_config.output_type in self.HELPER_RECOMMENDATIONS:
            helpers.extend(self.HELPER_RECOMMENDATIONS[job_config.output_type])

        # Additional helpers based on references
        for ref in job_config.references:
            if ref.type == "style" and HelperPass.IP_ADAPTER not in helpers:
                helpers.append(HelperPass.IP_ADAPTER)
            elif ref.type == "color" and HelperPass.COLOR_PALETTE not in helpers:
                helpers.append(HelperPass.COLOR_PALETTE)
            elif ref.type == "composition" and HelperPass.DEPTH_MAP not in helpers:
                helpers.append(HelperPass.DEPTH_MAP)

        # Add palette enforcement if color constraints specified
        if (job_config.style_constraints and
            job_config.style_constraints.color_palette and
            HelperPass.COLOR_PALETTE not in helpers):
            helpers.append(HelperPass.COLOR_PALETTE)

        # Remove duplicates while preserving order
        seen = set()
        unique_helpers = []
        for h in helpers:
            if h not in seen:
                seen.add(h)
                unique_helpers.append(h)

        return unique_helpers

    def _estimate_time(
        self,
        job_config: JobConfig,
        helpers: List[HelperPass]
    ) -> float:
        """
        Estimate generation time in minutes.

        Factors:
        - Quality preset
        - Number of passes
        - Helper passes
        - Resolution
        - Number of diffusion steps
        """
        base_time = self.BASE_TIME_ESTIMATES[job_config.quality_preset]

        # Multiply by number of passes
        if job_config.multi_pass_enabled:
            base_time *= job_config.num_passes

        # Add time for each helper pass
        helper_time = len(helpers) * 0.5  # ~30 seconds per helper

        # Adjust for resolution
        pixels = job_config.aspect_ratio.width * job_config.aspect_ratio.height
        resolution_factor = pixels / (512 * 512)  # Normalize to 512x512
        base_time *= resolution_factor

        # Adjust for diffusion steps
        steps_factor = job_config.generation_params.steps / 30  # Normalize to 30 steps
        base_time *= steps_factor

        total_time = base_time + helper_time

        return round(total_time, 2)

    def _estimate_memory(
        self,
        job_config: JobConfig,
        helpers: List[HelperPass]
    ) -> float:
        """
        Estimate peak memory usage in GB.

        Factors:
        - Quality preset
        - Resolution
        - Helper passes
        - Number of concurrent operations
        """
        base_memory = self.BASE_MEMORY_ESTIMATES[job_config.quality_preset]

        # Add memory for helpers
        helper_memory = len(helpers) * 0.5  # ~500MB per helper

        # Adjust for resolution
        pixels = job_config.aspect_ratio.width * job_config.aspect_ratio.height
        resolution_factor = pixels / (512 * 512)
        base_memory *= (1 + (resolution_factor - 1) * 0.5)  # Partial scaling

        # Multi-pass adds small overhead
        if job_config.multi_pass_enabled:
            base_memory *= 1.1

        total_memory = base_memory + helper_memory

        return round(total_memory, 2)

    def _generate_optimization_notes(self, job_config: JobConfig) -> List[str]:
        """Generate optimization recommendations"""
        notes = []

        # Check if resolution is non-standard
        if (job_config.aspect_ratio.width % 64 != 0 or
            job_config.aspect_ratio.height % 64 != 0):
            notes.append(
                "⚠️ Resolution is not a multiple of 64. Consider adjusting for "
                "optimal performance (e.g., 512x512, 768x768, 1024x1024)"
            )

        # Check diffusion steps
        steps = job_config.generation_params.steps
        if steps < 20:
            notes.append(
                "ℹ️ Low step count (<20) may result in lower quality. "
                "Consider increasing for better results."
            )
        elif steps > 50:
            notes.append(
                "ℹ️ High step count (>50) may not improve quality significantly. "
                "Consider reducing for faster generation."
            )

        # Check guidance scale
        guidance = job_config.generation_params.guidance_scale
        if guidance < 5:
            notes.append(
                "ℹ️ Low guidance scale (<5) may produce unpredictable results."
            )
        elif guidance > 15:
            notes.append(
                "ℹ️ High guidance scale (>15) may cause over-saturation or artifacts."
            )

        # Check multi-pass configuration
        if job_config.multi_pass_enabled and job_config.num_passes > 5:
            notes.append(
                "💡 High pass count (>5) increases generation time. "
                "Consider using 3-5 passes for most use cases."
            )

        # Check validation thresholds
        val_req = job_config.validation_requirements
        if all([
            val_req.min_sharpness_score > 0.85,
            val_req.min_anatomy_score > 0.85,
            val_req.min_prompt_alignment > 0.85
        ]):
            notes.append(
                "⚠️ Very high validation thresholds (>0.85) may result in many "
                "rejections. Consider relaxing thresholds or increasing pass count."
            )

        return notes

    def _check_warnings(self, job_config: JobConfig) -> List[str]:
        """Check for potential issues in configuration"""
        warnings = []

        # Check memory requirements
        pixels = job_config.aspect_ratio.width * job_config.aspect_ratio.height
        if pixels > 1024 * 1024:  # > 1 megapixel
            warnings.append(
                "⚠️ High resolution (>1MP) may cause out-of-memory errors. "
                "Ensure adequate GPU memory available."
            )

        # Check for conflicting style constraints
        if job_config.style_constraints:
            sc = job_config.style_constraints
            if sc.color_temperature == "warm" and sc.saturation_level == "low":
                warnings.append(
                    "ℹ️ Warm color temperature with low saturation may produce "
                    "muted results."
                )

        # Check negative prompt
        if (job_config.output_type in [OutputType.CHARACTER_2D, OutputType.CHARACTER_3D]
            and not job_config.negative_prompt):
            warnings.append(
                "💡 Consider adding negative prompts for character generation "
                "(e.g., 'bad anatomy, extra limbs, deformed')"
            )

        # Check seed for reproducibility
        if (job_config.generation_params.seed is None and
            job_config.multi_pass_enabled):
            warnings.append(
                "ℹ️ No seed specified. Multi-pass results will be non-deterministic."
            )

        return warnings

    def create_simple_job(
        self,
        name: str,
        prompt: str,
        output_type: OutputType = OutputType.CHARACTER_2D,
        render_style: RenderStyle = RenderStyle.ANIME,
        quality: QualityPreset = QualityPreset.STANDARD,
        width: int = 512,
        height: int = 512,
        multi_pass: bool = False,
        num_passes: int = 3,
        **kwargs
    ) -> JobConfig:
        """
        Create a simple job configuration with minimal parameters.

        Args:
            name: Job name
            prompt: Generation prompt
            output_type: Type of output
            render_style: Rendering style
            quality: Quality preset
            width: Image width
            height: Image height
            multi_pass: Enable multi-pass generation
            num_passes: Number of passes
            **kwargs: Additional parameters

        Returns:
            JobConfig instance
        """
        job_id = f"job_{uuid.uuid4().hex[:8]}"

        config = JobConfig(
            id=job_id,
            name=name,
            main_prompt=prompt,
            output_type=output_type,
            render_style=render_style,
            quality_preset=quality,
            aspect_ratio=AspectRatio(width=width, height=height),
            multi_pass_enabled=multi_pass,
            num_passes=num_passes,
            lineage=LineageConfig(job_id=job_id),
            **kwargs
        )

        return config

    def create_batch_jobs(
        self,
        base_config: JobConfig,
        variations: List[Dict[str, Any]],
    ) -> List[JobConfig]:
        """
        Create batch jobs from a base configuration with variations.

        Args:
            base_config: Base job configuration
            variations: List of dictionaries with parameter variations

        Returns:
            List of JobConfig instances
        """
        jobs = []

        for i, variation in enumerate(variations):
            # Create copy of base config
            config_dict = base_config.to_dict()

            # Apply variations
            config_dict.update(variation)

            # Generate unique ID
            config_dict["id"] = f"{base_config.id}_var{i+1:03d}"
            config_dict["name"] = f"{base_config.name} - Variation {i+1}"

            # Update lineage
            if "lineage" not in variation:
                config_dict["lineage"]["job_id"] = config_dict["id"]

            jobs.append(JobConfig.from_dict(config_dict))

        return jobs
