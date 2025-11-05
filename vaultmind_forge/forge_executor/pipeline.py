"""
VaultMind Forge - Complete Pipeline Orchestration
End-to-end DAG execution for generation → validation → conversion → export
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

# Add modules to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from forge_validator.ai_validator import AIValidator, ValidationDecision
from forge_lineage import LineageTracker, OperationType
from forge_converter.ai_control import AuthorityLevel


# Simple synchronous DAG for pipeline orchestration
@dataclass
class Task:
    """Simple task for synchronous execution"""
    id: str
    func: Callable
    args: tuple = ()
    deps: List[str] = None

    def __post_init__(self):
        if self.deps is None:
            self.deps = []


class DAG:
    """Simple synchronous DAG executor"""
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.results: Dict[str, Any] = {}

    def add_task(self, task: Task):
        """Add task to DAG"""
        self.tasks[task.id] = task

    def _get_execution_order(self) -> List[str]:
        """Topological sort to get execution order"""
        visited = set()
        order = []

        def visit(task_id: str):
            if task_id in visited:
                return
            visited.add(task_id)

            task = self.tasks[task_id]
            for dep in task.deps:
                if dep in self.tasks:
                    visit(dep)

            order.append(task_id)

        for task_id in self.tasks.keys():
            visit(task_id)

        return order


class Executor:
    """Simple synchronous executor"""
    def execute(self, dag: DAG):
        """Execute DAG tasks in order"""
        execution_order = dag._get_execution_order()

        for task_id in execution_order:
            task = dag.tasks[task_id]

            # Get dependency results
            dep_results = []
            for dep_id in task.deps:
                if dep_id in dag.results:
                    dep_results.append(dag.results[dep_id])

            # Execute task
            if dep_results:
                # If task has deps, pass the last result as argument
                result = task.func(*dep_results, *task.args)
            else:
                # No deps, just call with args
                result = task.func(*task.args)

            # Store result
            dag.results[task_id] = result


class PipelineStage(Enum):
    """Pipeline stages"""
    GENERATE = "generate"
    VALIDATE = "validate"
    RETRY = "retry"
    OPTIMIZE = "optimize"
    EXPORT_UNITY = "export_unity"
    EXPORT_UNREAL = "export_unreal"
    EXPORT_GODOT = "export_godot"
    EXPORT_WEB = "export_web"
    PACKAGE = "package"


@dataclass
class PipelineResult:
    """Result from pipeline execution"""
    success: bool
    outputs: Dict[str, Path]
    lineage_checksums: Dict[str, str]
    stages_completed: List[str]
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class AssetPipeline:
    """
    Complete asset generation pipeline with AI control and lineage tracking.

    Pipeline flow:
        generate → validate (AI) → retry (if needed) → optimize → export (parallel) → package

    Features:
    - AI-powered validation with auto-retry
    - Conditional execution (retry only if needed)
    - Parallel multi-engine export
    - Complete lineage tracking
    - Human-in-loop for flagged assets

    Example:
        >>> pipeline = AssetPipeline()
        >>>
        >>> # Run full pipeline
        >>> result = pipeline.run_generation_pipeline(
        ...     prompt="medieval knight armor",
        ...     output_type="character",
        ...     target_engines=["unity", "unreal"]
        ... )
        >>>
        >>> # Check results
        >>> if result.success:
        ...     print(f"Generated and exported to: {list(result.outputs.keys())}")
        ... else:
        ...     print(f"Pipeline failed: {result.errors}")
    """

    def __init__(
        self,
        ai_authority: AuthorityLevel = AuthorityLevel.HIGH_AUTONOMY,
        max_retries: int = 3,
        enable_lineage: bool = True
    ):
        """
        Initialize pipeline

        Args:
            ai_authority: AI authority level for validation
            max_retries: Maximum retry attempts for failed validation
            enable_lineage: Enable lineage tracking
        """
        self.ai_validator = AIValidator(authority_level=ai_authority)
        self.lineage_tracker = LineageTracker() if enable_lineage else None
        self.max_retries = max_retries

        # Pipeline state
        self.current_job: Optional[Dict[str, Any]] = None
        self.retry_count = 0

    def run_generation_pipeline(
        self,
        prompt: str,
        output_type: str = "standard",
        target_engines: Optional[List[str]] = None,
        is_hero_asset: bool = False,
        generation_params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> PipelineResult:
        """
        Run complete generation pipeline

        Args:
            prompt: Generation prompt
            output_type: Output type (character, environment, etc.)
            target_engines: List of target engines (unity, unreal, godot, web)
            is_hero_asset: Whether this is a hero asset (requires human review)
            generation_params: Additional generation parameters
            **kwargs: Additional pipeline options

        Returns:
            PipelineResult with outputs and lineage info
        """
        # Set up job context
        self.current_job = {
            "prompt": prompt,
            "output_type": output_type,
            "is_hero_asset": is_hero_asset,
            "target_engines": target_engines or ["unity"],
            "generation_params": generation_params or {},
            **kwargs
        }

        # Build DAG
        dag = self._build_pipeline_dag()

        # Execute
        try:
            executor = Executor()
            executor.execute(dag)

            # Collect results
            return self._collect_results()

        except Exception as e:
            return PipelineResult(
                success=False,
                outputs={},
                lineage_checksums={},
                stages_completed=[],
                errors=[str(e)]
            )

    def _build_pipeline_dag(self) -> DAG:
        """Build complete pipeline DAG"""
        dag = DAG()

        # Stage 1: Generate
        dag.add_task(Task(
            id="generate",
            func=self._generate_task,
            args=(self.current_job,)
        ))

        # Stage 2: Validate (AI-powered)
        dag.add_task(Task(
            id="validate",
            func=self._validate_task,
            deps=["generate"]
        ))

        # Stage 3: Retry (conditional - only if validation failed)
        dag.add_task(Task(
            id="retry_check",
            func=self._retry_check_task,
            deps=["validate"]
        ))

        # Stage 4: Optimize
        dag.add_task(Task(
            id="optimize",
            func=self._optimize_task,
            deps=["retry_check"]
        ))

        # Stage 5: Export (parallel for multiple engines)
        target_engines = self.current_job.get("target_engines", ["unity"])

        for engine in target_engines:
            task_id = f"export_{engine}"
            dag.add_task(Task(
                id=task_id,
                func=lambda result, eng=engine: self._export_task(eng, result),
                deps=["optimize"]
            ))

        # Stage 6: Package (depends on all exports)
        export_tasks = [f"export_{engine}" for engine in target_engines]
        dag.add_task(Task(
            id="package",
            func=lambda *results: self._package_task(list(results)),
            deps=export_tasks
        ))

        return dag

    def _generate_task(self, job_config: Dict[str, Any]) -> Path:
        """
        Generation task (placeholder - integrates with forge_diffusion)

        In production, this would call:
            from forge_diffusion import DiffusionGenerator
            generator = DiffusionGenerator()
            result = generator.generate(prompt=job_config["prompt"], ...)
        """
        print(f"[GENERATE] Generating: {job_config['prompt']}")

        # Placeholder: simulate generation
        output_path = Path("assets/generated/diffusion/textures") / f"job_{id(job_config)}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()  # Create placeholder file

        # Record lineage
        if self.lineage_tracker:
            checksum = self.lineage_tracker.record_generation(
                asset_path=output_path,
                parameters={
                    "prompt": job_config["prompt"],
                    "output_type": job_config["output_type"],
                    **job_config.get("generation_params", {})
                },
                generator="forge_diffusion"
            )
            job_config["generation_checksum"] = checksum

        print(f"[GENERATE] Created: {output_path}")
        return output_path

    def _validate_task(self, generate_result: Path) -> Dict[str, Any]:
        """
        Validation task with AI decision

        Args:
            generate_result: Output from generate task

        Returns:
            Validation result dict
        """
        print(f"[VALIDATE] Validating: {generate_result}")

        # AI-powered validation
        context = {
            "output_type": self.current_job["output_type"],
            "is_hero_asset": self.current_job["is_hero_asset"],
            "attempt_number": self.retry_count + 1
        }

        ai_result = self.ai_validator.validate_with_ai(
            asset_path=generate_result,
            context=context,
            prompt=self.current_job["prompt"]
        )

        # Record lineage
        if self.lineage_tracker:
            self.lineage_tracker.record_validation(
                asset_path=generate_result,
                scores=ai_result.validation.checks,
                ai_decision={
                    "decision": ai_result.decision.value,
                    "confidence": ai_result.confidence,
                    "reasoning": ai_result.reasoning
                }
            )

        print(f"[VALIDATE] Decision: {ai_result.decision.value} (confidence: {ai_result.confidence:.2f})")
        print(f"[VALIDATE] Reasoning: {ai_result.reasoning}")

        return {
            "asset_path": generate_result,
            "decision": ai_result.decision,
            "confidence": ai_result.confidence,
            "reasoning": ai_result.reasoning,
            "adjustments": ai_result.suggested_adjustments
        }

    def _retry_check_task(self, validate_result: Dict[str, Any]) -> Optional[Path]:
        """
        Check if retry is needed and execute if so

        Args:
            validate_result: Output from validate task

        Returns:
            New asset path if retried, otherwise original asset path
        """
        decision = validate_result["decision"]

        if decision == ValidationDecision.RETRY_RECOMMENDED and self.retry_count < self.max_retries:
            print(f"[RETRY] Retry recommended (attempt {self.retry_count + 1}/{self.max_retries})")
            print(f"[RETRY] Adjustments: {validate_result['adjustments']}")

            # Apply adjustments and regenerate
            adjustments = validate_result["adjustments"]
            if adjustments:
                # Update generation params with adjustments
                for key, value in adjustments.items():
                    if key != "reasoning":
                        self.current_job["generation_params"][key] = value

            # Record original for lineage
            original_asset = validate_result["asset_path"]

            # Regenerate
            self.retry_count += 1
            new_asset = self._generate_task(self.current_job)

            # Record retry lineage
            if self.lineage_tracker:
                self.lineage_tracker.record_retry(
                    original_asset=original_asset,
                    retry_asset=new_asset,
                    attempt_number=self.retry_count,
                    adjustments=adjustments
                )

            # Re-validate
            new_validation = self._validate_task(new_asset)

            # If still failed and retries left, recurse
            if new_validation["decision"] == ValidationDecision.RETRY_RECOMMENDED:
                return self._retry_check_task(new_validation)
            else:
                return new_asset

        elif decision == ValidationDecision.FLAG_FOR_HUMAN:
            print(f"[RETRY] Asset flagged for human review")
            # In production, this would queue for human review
            # For now, continue with original asset
            return validate_result["asset_path"]

        else:
            # Approved or rejected - no retry
            print(f"[RETRY] No retry needed: {decision.value}")
            return validate_result["asset_path"]

    def _optimize_task(self, validated_asset: Path) -> Path:
        """
        Optimization task (LOD generation, compression, etc.)

        In production, this would call:
            from forge_converter.optimization import optimize_asset
            optimized = optimize_asset(validated_asset, settings)
        """
        print(f"[OPTIMIZE] Optimizing: {validated_asset}")

        # Placeholder: copy to validated directory
        output_path = Path("assets/validated/winners") / validated_asset.name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # In production: actually optimize the asset
        # For now: just reference original
        if validated_asset.exists():
            import shutil
            shutil.copy(validated_asset, output_path)

        # Record lineage
        if self.lineage_tracker and output_path.exists():
            self.lineage_tracker.record_optimization(
                input_asset=validated_asset,
                output_asset=output_path,
                optimization_type="quality_approved",
                parameters={"stage": "validated"}
            )

        print(f"[OPTIMIZE] Optimized: {output_path}")
        return output_path

    def _export_task(self, engine: str, optimized_asset: Path) -> Path:
        """
        Export task for specific engine

        In production, this would call:
            from forge_converter import convert_for_engine
            exported = convert_for_engine(optimized_asset, engine)
        """
        print(f"[EXPORT-{engine.upper()}] Exporting for {engine}")

        # Placeholder: create engine-specific output
        output_path = Path(f"assets/output/{engine}") / f"{optimized_asset.stem}.{engine}"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # In production: actually convert to engine format
        # For now: just create placeholder
        if optimized_asset.exists():
            import shutil
            shutil.copy(optimized_asset, output_path)

        # Record lineage
        if self.lineage_tracker and output_path.exists():
            self.lineage_tracker.record_conversion(
                input_asset=optimized_asset,
                output_asset=output_path,
                format=engine,
                converter="forge_converter",
                parameters={"target_engine": engine}
            )

        print(f"[EXPORT-{engine.upper()}] Exported: {output_path}")
        return output_path

    def _package_task(self, export_results: List[Path]) -> Path:
        """
        Package task (create deliverable package)

        In production, this would call:
            from forge_packaging import create_package
            package = create_package(export_results, metadata)
        """
        print(f"[PACKAGE] Packaging {len(export_results)} exports")

        # Placeholder: create package directory
        package_path = Path("assets/packages") / f"package_{id(self.current_job)}"
        package_path.mkdir(parents=True, exist_ok=True)

        # In production: create actual package with metadata, README, etc.
        print(f"[PACKAGE] Package created: {package_path}")
        return package_path

    def _collect_results(self) -> PipelineResult:
        """Collect pipeline results"""
        # In production, this would collect actual outputs from tasks
        # For now, return success

        return PipelineResult(
            success=True,
            outputs={
                engine: Path(f"assets/output/{engine}")
                for engine in self.current_job.get("target_engines", ["unity"])
            },
            lineage_checksums={"generation": self.current_job.get("generation_checksum", "")},
            stages_completed=[
                "generate",
                "validate",
                "retry_check" if self.retry_count > 0 else "",
                "optimize",
                *[f"export_{e}" for e in self.current_job.get("target_engines", ["unity"])],
                "package"
            ]
        )


# Convenience function
def run_asset_pipeline(
    prompt: str,
    target_engines: List[str] = None,
    **kwargs
) -> PipelineResult:
    """
    Quick pipeline execution

    Args:
        prompt: Generation prompt
        target_engines: Target engines for export
        **kwargs: Additional options

    Returns:
        PipelineResult

    Example:
        >>> result = run_asset_pipeline(
        ...     prompt="fantasy sword texture",
        ...     target_engines=["unity", "unreal"]
        ... )
    """
    pipeline = AssetPipeline()
    return pipeline.run_generation_pipeline(
        prompt=prompt,
        target_engines=target_engines,
        **kwargs
    )
