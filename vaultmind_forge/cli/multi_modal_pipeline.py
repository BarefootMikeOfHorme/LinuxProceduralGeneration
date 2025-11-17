"""
Multi-Modal Generation Pipeline Orchestrator

Rembrandt-level sophistication:
- Simultaneous multi-modal generation (image, audio, text)
- Intelligent cross-modal validation and consistency
- Adaptive resource allocation
- Modal synchronization and timing
- Quality-driven iterative refinement
- Cross-modal enhancement (text informs image, image informs audio, etc.)
"""

from __future__ import annotations

import asyncio
import anyio
import time
import uuid
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .workflow_engine import Workflow, Task, TaskType, WorkflowEngine
from .agent_manager import AgentType, AgentManager
from .terminal_ui import TerminalUI, console


class Modality(str, Enum):
    """Supported generation modalities"""
    IMAGE = "image"
    AUDIO = "audio"
    TEXT = "text"
    VIDEO = "video"
    MESH_3D = "mesh_3d"


class ModalQuality(str, Enum):
    """Quality tiers for modal generation"""
    DRAFT = "draft"          # Fast, low quality
    STANDARD = "standard"    # Balanced
    HIGH = "high"           # High quality
    MASTERPIECE = "masterpiece"  # Maximum quality, Rembrandt-style


@dataclass
class ModalSpec:
    """Specification for a single modality"""
    modality: Modality
    quality: ModalQuality
    params: Dict[str, Any] = field(default_factory=dict)

    # Resource requirements
    estimated_duration: float = 30.0
    requires_gpu: bool = False
    priority: int = 5  # 1-10, higher = more important

    # Dependencies on other modalities
    depends_on_modalities: List[Modality] = field(default_factory=list)

    # Enhancement from other modalities
    enhanced_by: List[Modality] = field(default_factory=list)


@dataclass
class ModalResult:
    """Result from modal generation"""
    modality: Modality
    success: bool
    output_path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0  # 0.0-1.0
    generation_time: float = 0.0
    error: Optional[str] = None

    # Cross-modal validation
    consistency_scores: Dict[Modality, float] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Complete multi-modal pipeline result"""
    pipeline_id: str
    modal_results: Dict[Modality, ModalResult]
    overall_quality: float  # Weighted average
    total_duration: float
    consistency_score: float  # Cross-modal consistency
    success: bool
    refinement_iterations: int = 0


class MultiModalPipeline:
    """
    Orchestrates multi-modal generation with cross-modal intelligence

    Like Rembrandt's mastery across painting, etching, and drawing -
    each modality informs and enhances the others
    """

    def __init__(
        self,
        workflow_engine: WorkflowEngine,
        agent_manager: AgentManager,
    ):
        self.workflow_engine = workflow_engine
        self.agent_manager = agent_manager

        # Pipeline state
        self.active_pipelines: Dict[str, Dict[str, Any]] = {}

        # Cross-modal enhancement rules
        self.enhancement_rules = self._build_enhancement_rules()

        # Quality thresholds
        self.quality_thresholds = {
            ModalQuality.DRAFT: 0.5,
            ModalQuality.STANDARD: 0.7,
            ModalQuality.HIGH: 0.85,
            ModalQuality.MASTERPIECE: 0.95,
        }

    def _build_enhancement_rules(self) -> Dict[Modality, Dict[str, Any]]:
        """
        Build rules for how modalities enhance each other

        Rembrandt's understanding that each medium brings unique insights
        """
        return {
            Modality.IMAGE: {
                "enhanced_by": {
                    Modality.TEXT: {
                        "type": "prompt_refinement",
                        "weight": 0.8,
                        "description": "Text descriptions provide detailed guidance for image generation",
                    },
                    Modality.AUDIO: {
                        "type": "mood_extraction",
                        "weight": 0.4,
                        "description": "Audio mood informs image atmosphere and color palette",
                    },
                },
                "enhances": {
                    Modality.AUDIO: {
                        "type": "visual_to_sonic",
                        "description": "Image composition informs audio structure",
                    },
                    Modality.TEXT: {
                        "type": "visual_description",
                        "description": "Generated image inspires descriptive text",
                    },
                },
            },
            Modality.AUDIO: {
                "enhanced_by": {
                    Modality.TEXT: {
                        "type": "lyrical_guidance",
                        "weight": 0.7,
                    },
                    Modality.IMAGE: {
                        "type": "visual_mood",
                        "weight": 0.5,
                    },
                },
            },
            Modality.TEXT: {
                "enhanced_by": {
                    Modality.IMAGE: {
                        "type": "visual_inspiration",
                        "weight": 0.6,
                    },
                    Modality.AUDIO: {
                        "type": "sonic_atmosphere",
                        "weight": 0.4,
                    },
                },
            },
        }

    async def create_pipeline(
        self,
        name: str,
        description: str,
        modalities: List[ModalSpec],
        target_quality: ModalQuality = ModalQuality.STANDARD,
        max_refinement_iterations: int = 3,
    ) -> str:
        """
        Create multi-modal generation pipeline

        Like Rembrandt planning a complex composition - each element
        considered in relation to the whole
        """
        pipeline_id = f"mmp_{uuid.uuid4().hex[:8]}"

        # Validate modalities
        self._validate_modal_specs(modalities)

        # Build execution plan
        execution_plan = self._build_execution_plan(modalities)

        # Create workflow
        workflow = self.workflow_engine.create_workflow(
            name=f"Multi-Modal: {name}",
            description=description,
            max_parallel=len(modalities),  # All modalities can run in parallel if no dependencies
        )

        # Store pipeline state
        self.active_pipelines[pipeline_id] = {
            "workflow_id": workflow.id,
            "name": name,
            "description": description,
            "modalities": modalities,
            "target_quality": target_quality,
            "max_refinement_iterations": max_refinement_iterations,
            "execution_plan": execution_plan,
            "results": {},
            "refinement_count": 0,
            "status": "created",
        }

        return pipeline_id

    def _validate_modal_specs(self, modalities: List[ModalSpec]) -> None:
        """Validate modal specifications"""
        if not modalities:
            raise ValueError("At least one modality required")

        # Check for circular dependencies
        modal_set = {spec.modality for spec in modalities}
        for spec in modalities:
            for dep in spec.depends_on_modalities:
                if dep not in modal_set:
                    raise ValueError(f"{spec.modality} depends on {dep} which is not in pipeline")

    def _build_execution_plan(self, modalities: List[ModalSpec]) -> Dict[str, Any]:
        """
        Build optimal execution plan considering dependencies and enhancements

        Rembrandt's meticulous planning - what to paint first, what builds on what
        """
        # Sort by dependencies (topological sort)
        sorted_modalities = self._topological_sort_modalities(modalities)

        # Identify parallel execution groups
        execution_groups = self._identify_parallel_groups(sorted_modalities)

        # Calculate critical path
        critical_path_duration = sum(
            max(spec.estimated_duration for spec in group)
            for group in execution_groups
        )

        return {
            "sorted_modalities": sorted_modalities,
            "execution_groups": execution_groups,
            "critical_path_duration": critical_path_duration,
            "parallelism_factor": len(modalities) / len(execution_groups) if execution_groups else 1,
        }

    def _topological_sort_modalities(self, modalities: List[ModalSpec]) -> List[ModalSpec]:
        """Sort modalities by dependencies"""
        # Build dependency graph
        graph: Dict[Modality, Set[Modality]] = {spec.modality: set(spec.depends_on_modalities) for spec in modalities}
        specs_by_modality = {spec.modality: spec for spec in modalities}

        # Kahn's algorithm
        in_degree = {modality: len(deps) for modality, deps in graph.items()}
        queue = [modality for modality, degree in in_degree.items() if degree == 0]
        sorted_list = []

        while queue:
            current = queue.pop(0)
            sorted_list.append(specs_by_modality[current])

            # Reduce in-degree for dependent modalities
            for modality, deps in graph.items():
                if current in deps:
                    in_degree[modality] -= 1
                    if in_degree[modality] == 0:
                        queue.append(modality)

        if len(sorted_list) != len(modalities):
            raise ValueError("Circular dependency detected in modalities")

        return sorted_list

    def _identify_parallel_groups(self, sorted_modalities: List[ModalSpec]) -> List[List[ModalSpec]]:
        """Identify which modalities can execute in parallel"""
        groups = []
        processed = set()

        for spec in sorted_modalities:
            # Can this spec run in parallel with current group?
            if not groups or any(dep in processed for dep in spec.depends_on_modalities):
                # Start new group
                groups.append([spec])
            else:
                # Add to current group
                groups[-1].append(spec)

            processed.add(spec.modality)

        return groups

    async def execute_pipeline(
        self,
        pipeline_id: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> PipelineResult:
        """
        Execute multi-modal pipeline with iterative refinement

        Like Rembrandt's layered approach - building up the masterpiece
        through careful iteration
        """
        pipeline = self.active_pipelines.get(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        pipeline["status"] = "executing"
        start_time = time.time()

        # Execute each group in sequence, modalities within group in parallel
        for group_idx, group in enumerate(pipeline["execution_plan"]["execution_groups"]):
            console.print(f"\n[cyan]Executing Group {group_idx + 1}/{len(pipeline['execution_plan']['execution_groups'])}[/cyan]")

            # Execute group in parallel
            group_results = await self._execute_modal_group(
                pipeline_id,
                group,
                progress_callback,
            )

            # Store results
            for modality, result in group_results.items():
                pipeline["results"][modality] = result

        # Validate cross-modal consistency
        consistency_score = self._validate_cross_modal_consistency(pipeline["results"])

        # Check if refinement needed
        overall_quality = self._calculate_overall_quality(pipeline["results"])
        target_threshold = self.quality_thresholds[pipeline["target_quality"]]

        # Iterative refinement
        while (
            (overall_quality < target_threshold or consistency_score < 0.8)
            and pipeline["refinement_count"] < pipeline["max_refinement_iterations"]
        ):
            console.print(f"\n[yellow]Quality {overall_quality:.2%} below target {target_threshold:.2%}. Refining...[/yellow]")

            pipeline["refinement_count"] += 1

            # Identify modalities needing refinement
            modalities_to_refine = self._identify_refinement_targets(
                pipeline["results"],
                target_threshold,
            )

            # Refine with cross-modal enhancement
            refined_results = await self._refine_modalities(
                pipeline_id,
                modalities_to_refine,
                pipeline["results"],
            )

            # Update results
            pipeline["results"].update(refined_results)

            # Re-validate
            consistency_score = self._validate_cross_modal_consistency(pipeline["results"])
            overall_quality = self._calculate_overall_quality(pipeline["results"])

        total_duration = time.time() - start_time
        pipeline["status"] = "completed"

        return PipelineResult(
            pipeline_id=pipeline_id,
            modal_results=pipeline["results"],
            overall_quality=overall_quality,
            total_duration=total_duration,
            consistency_score=consistency_score,
            success=all(r.success for r in pipeline["results"].values()),
            refinement_iterations=pipeline["refinement_count"],
        )

    async def _execute_modal_group(
        self,
        pipeline_id: str,
        group: List[ModalSpec],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]],
    ) -> Dict[Modality, ModalResult]:
        """Execute a group of modalities in parallel"""
        # Create tasks for parallel execution
        tasks = []
        for spec in group:
            task = self._execute_modality(pipeline_id, spec)
            tasks.append((spec.modality, task))

        # Execute in parallel
        results = {}
        for modality, task in tasks:
            result = await task
            results[modality] = result

            if progress_callback:
                progress_callback({
                    "pipeline_id": pipeline_id,
                    "modality": modality,
                    "result": result,
                })

        return results

    async def _execute_modality(
        self,
        pipeline_id: str,
        spec: ModalSpec,
    ) -> ModalResult:
        """
        Execute generation for a single modality

        Each modality executed with the care Rembrandt gave each brushstroke
        """
        start_time = time.time()

        console.print(f"  [green]Generating {spec.modality.value}...[/green]")

        # Simulate generation (in production, this calls actual generators)
        # For image: SDXL, for audio: MusicGen, for text: GPT, etc.
        await anyio.sleep(spec.estimated_duration / 10)  # Simulated for demo

        # Mock result
        result = ModalResult(
            modality=spec.modality,
            success=True,
            output_path=Path(f"output/{pipeline_id}_{spec.modality.value}.png"),
            metadata={
                "quality": spec.quality.value,
                "params": spec.params,
            },
            quality_score=0.75 + (0.2 * hash(spec.modality.value) % 100 / 100),  # Mock score
            generation_time=time.time() - start_time,
        )

        console.print(f"  [green][OK][/green] {spec.modality.value} complete (quality: {result.quality_score:.2%})")

        return result

    def _validate_cross_modal_consistency(self, results: Dict[Modality, ModalResult]) -> float:
        """
        Validate consistency across modalities

        Rembrandt ensuring harmony across all elements of composition
        """
        if len(results) < 2:
            return 1.0  # Single modality is always consistent

        consistency_scores = []

        # Check each pair of modalities
        modalities = list(results.keys())
        for i, mod1 in enumerate(modalities):
            for mod2 in modalities[i+1:]:
                # Calculate consistency between these modalities
                score = self._calculate_modal_consistency(
                    results[mod1],
                    results[mod2],
                )
                consistency_scores.append(score)

        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 1.0

    def _calculate_modal_consistency(
        self,
        result1: ModalResult,
        result2: ModalResult,
    ) -> float:
        """Calculate consistency score between two modal results"""
        # In production: use AI to analyze semantic consistency
        # For now: mock based on quality scores
        return min(result1.quality_score, result2.quality_score) * 0.9

    def _calculate_overall_quality(self, results: Dict[Modality, ModalResult]) -> float:
        """Calculate weighted overall quality"""
        if not results:
            return 0.0

        total_score = sum(r.quality_score for r in results.values())
        return total_score / len(results)

    def _identify_refinement_targets(
        self,
        results: Dict[Modality, ModalResult],
        target_threshold: float,
    ) -> List[Modality]:
        """Identify which modalities need refinement"""
        targets = []

        for modality, result in results.items():
            if result.quality_score < target_threshold:
                targets.append(modality)

        return targets

    async def _refine_modalities(
        self,
        pipeline_id: str,
        modalities_to_refine: List[Modality],
        existing_results: Dict[Modality, ModalResult],
    ) -> Dict[Modality, ModalResult]:
        """
        Refine modalities using cross-modal enhancement

        Like Rembrandt's final touches, informed by the whole composition
        """
        refined_results = {}

        for modality in modalities_to_refine:
            console.print(f"  [yellow]Refining {modality.value}...[/yellow]")

            # Apply cross-modal enhancements
            enhancement_context = self._build_enhancement_context(
                modality,
                existing_results,
            )

            # Re-generate with enhancement context
            # In production: pass enhancement_context to generator
            await anyio.sleep(1)  # Simulated refinement

            # Mock refined result with improved quality
            original = existing_results[modality]
            refined_results[modality] = ModalResult(
                modality=modality,
                success=True,
                output_path=original.output_path,
                metadata=original.metadata,
                quality_score=min(original.quality_score + 0.15, 1.0),  # Improved
                generation_time=original.generation_time + 1.0,
            )

            console.print(f"  [green][OK][/green] {modality.value} refined (quality: {refined_results[modality].quality_score:.2%})")

        return refined_results

    def _build_enhancement_context(
        self,
        target_modality: Modality,
        existing_results: Dict[Modality, ModalResult],
    ) -> Dict[str, Any]:
        """Build cross-modal enhancement context"""
        context = {}

        rules = self.enhancement_rules.get(target_modality, {}).get("enhanced_by", {})

        for source_modality, enhancement_spec in rules.items():
            if source_modality in existing_results:
                context[source_modality.value] = {
                    "type": enhancement_spec["type"],
                    "weight": enhancement_spec["weight"],
                    "result": existing_results[source_modality],
                }

        return context

    def visualize_pipeline(self, pipeline_id: str) -> None:
        """Visualize multi-modal pipeline"""
        pipeline = self.active_pipelines.get(pipeline_id)
        if not pipeline:
            console.print(f"[red]Pipeline {pipeline_id} not found[/red]")
            return

        TerminalUI.clear()
        TerminalUI.header("Multi-Modal Pipeline", pipeline["name"])

        console.print(f"[bold]Description:[/bold] {pipeline['description']}")
        console.print(f"[bold]Status:[/bold] {pipeline['status']}")
        console.print(f"[bold]Target Quality:[/bold] {pipeline['target_quality'].value}")
        console.print(f"[bold]Refinement Iterations:[/bold] {pipeline['refinement_count']}/{pipeline['max_refinement_iterations']}\\n")

        # Execution plan
        console.print("[cyan]Execution Plan:[/cyan]")
        for i, group in enumerate(pipeline["execution_plan"]["execution_groups"]):
            console.print(f"  Group {i+1}: {', '.join(spec.modality.value for spec in group)}")

        console.print(f"\\n[cyan]Estimated Duration:[/cyan] {pipeline['execution_plan']['critical_path_duration']:.1f}s")
        console.print(f"[cyan]Parallelism Factor:[/cyan] {pipeline['execution_plan']['parallelism_factor']:.2f}x\\n")

        # Results
        if pipeline["results"]:
            console.print("[green]Results:[/green]")
            for modality, result in pipeline["results"].items():
                status = "[OK]" if result.success else "[X]"
                console.print(f"  [{('green' if result.success else 'red')}]{status}[/] {modality.value}: {result.quality_score:.2%} quality")
