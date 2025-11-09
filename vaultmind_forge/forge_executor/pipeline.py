"""
VaultMind Forge - Complete Pipeline Orchestration
End-to-end DAG execution for generation → validation → conversion → export
"""

from __future__ import annotations

import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Add modules to path
sys.path.insert(0, str(Path(__file__).parents[1]))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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
    deps: List[str] = field(default_factory=list)
    timeout: Optional[float] = None  # Timeout in seconds
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[Exception] = None


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
    """Simple synchronous executor with error handling and progress tracking"""
    def execute(self, dag: DAG, on_progress: Optional[Callable[[str, str], None]] = None):
        """
        Execute DAG tasks in order

        Args:
            dag: DAG to execute
            on_progress: Optional callback for progress updates (task_id, status)

        Raises:
            RuntimeError: If task execution fails
        """
        execution_order = dag._get_execution_order()
        total_tasks = len(execution_order)
        completed_tasks = 0

        for task_id in execution_order:
            task = dag.tasks[task_id]

            # Notify progress
            if on_progress:
                on_progress(task_id, f"starting ({completed_tasks+1}/{total_tasks})")

            task.started_at = datetime.utcnow()
            logger.info(f"Executing task: {task_id} ({completed_tasks+1}/{total_tasks})")

            try:
                # Get dependency results
                dep_results = []
                for dep_id in task.deps:
                    if dep_id not in dag.results:
                        raise RuntimeError(f"Dependency '{dep_id}' failed or did not complete")
                    dep_results.append(dag.results[dep_id])

                # Execute task
                if dep_results:
                    # If task has deps, pass the last result as argument
                    result = task.func(*dep_results, *task.args)
                else:
                    # No deps, just call with args
                    result = task.func(*task.args)

                # Store result
                task.finished_at = datetime.utcnow()
                dag.results[task_id] = result
                completed_tasks += 1

                # Calculate execution time
                exec_time = (task.finished_at - task.started_at).total_seconds()
                logger.info(f"Task '{task_id}' completed successfully in {exec_time:.2f}s")

                if on_progress:
                    on_progress(task_id, f"completed ({completed_tasks}/{total_tasks})")

            except Exception as e:
                task.error = e
                task.finished_at = datetime.utcnow()
                logger.error(f"Task '{task_id}' failed: {str(e)}")

                if on_progress:
                    on_progress(task_id, f"failed: {str(e)}")

                raise RuntimeError(f"Task '{task_id}' failed: {str(e)}") from e


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
        enable_lineage: bool = True,
        base_path: Optional[Path] = None
    ):
        """
        Initialize pipeline

        Args:
            ai_authority: AI authority level for validation
            max_retries: Maximum retry attempts for failed validation
            enable_lineage: Enable lineage tracking
            base_path: Base path for asset storage (defaults to project assets directory)
        """
        self.ai_validator = AIValidator(authority_level=ai_authority)
        self.lineage_tracker = LineageTracker() if enable_lineage else None
        self.max_retries = max_retries

        # Define base paths
        if base_path is None:
            # Default to project assets directory
            base_path = Path(__file__).parents[2] / "assets"
        self.base_path = Path(base_path)

        # Define structured output paths for different asset types
        self.paths = {
            # Generation outputs by type
            'generated': {
                'textures': self.base_path / "generated" / "diffusion" / "textures",
                'models': self.base_path / "generated" / "diffusion" / "models",
                'materials': self.base_path / "generated" / "diffusion" / "materials",
                'animations': self.base_path / "generated" / "diffusion" / "animations",
                'environments': self.base_path / "generated" / "diffusion" / "environments",
                'characters': self.base_path / "generated" / "diffusion" / "characters",
                'props': self.base_path / "generated" / "diffusion" / "props",
                'effects': self.base_path / "generated" / "diffusion" / "effects",
                'audio': self.base_path / "generated" / "diffusion" / "audio",
                'standard': self.base_path / "generated" / "diffusion" / "standard"
            },
            # Validation outputs
            'validated': {
                'winners': self.base_path / "validated" / "winners",
                'rejected': self.base_path / "validated" / "rejected",
                'flagged': self.base_path / "validated" / "flagged_for_review"
            },
            # Engine-specific outputs
            'output': {
                'unity': self.base_path / "output" / "unity",
                'unreal': self.base_path / "output" / "unreal",
                'godot': self.base_path / "output" / "godot",
                'web': self.base_path / "output" / "web",
                'blender': self.base_path / "output" / "blender"
            },
            # Packaging and distribution
            'packages': self.base_path / "packages",
            'temp': self.base_path / "temp"
        }

        # Flatten and ensure all directories exist
        self._ensure_directories_exist()

        logger.info(f"Pipeline initialized with base path: {self.base_path}")

        # Pipeline state
        self.current_job: Optional[Dict[str, Any]] = None
        self.retry_count = 0

    def _ensure_directories_exist(self):
        """Create all required directories"""
        def create_dirs(path_dict):
            for key, value in path_dict.items():
                if isinstance(value, dict):
                    create_dirs(value)
                elif isinstance(value, Path):
                    value.mkdir(parents=True, exist_ok=True)
                    logger.debug(f"Created directory: {value}")

        create_dirs(self.paths)
        logger.info(f"All pipeline directories initialized")

    def get_path(self, category: str, subcategory: Optional[str] = None) -> Path:
        """
        Get a path from the pipeline structure

        Args:
            category: Main category (generated, validated, output, packages, temp)
            subcategory: Optional subcategory (textures, models, unity, etc.)

        Returns:
            Path object

        Example:
            >>> pipeline.get_path('generated', 'textures')
            PosixPath('/path/to/assets/generated/diffusion/textures')
        """
        if category not in self.paths:
            raise ValueError(f"Unknown category: {category}")

        path = self.paths[category]

        if subcategory:
            if isinstance(path, dict):
                if subcategory not in path:
                    raise ValueError(f"Unknown subcategory '{subcategory}' in '{category}'")
                return path[subcategory]
            else:
                raise ValueError(f"Category '{category}' has no subcategories")

        # If no subcategory and path is dict, return the dict itself (for iteration)
        # If no subcategory and path is Path, return the path
        return path

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
        logger.info(f"[GENERATE] Generating: {job_config['prompt']}")

        # Get output type and determine file extension
        output_type = job_config.get('output_type', 'standard')

        # Map output types to file extensions
        type_extensions = {
            'textures': '.png',
            'models': '.fbx',
            'materials': '.mtl',
            'animations': '.fbx',
            'environments': '.gltf',
            'characters': '.fbx',
            'props': '.fbx',
            'effects': '.vfx',
            'audio': '.wav',
            'standard': '.png'
        }

        # Get the proper path using the helper method
        output_dir = self.get_path('generated', output_type)

        # Generate unique filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        ext = type_extensions.get(output_type, '.png')
        output_path = output_dir / f"job_{timestamp}_{id(job_config)}{ext}"

        # Placeholder: simulate generation
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

        logger.info(f"[GENERATE] Created: {output_path}")
        return output_path

    def _validate_task(self, generate_result: Path) -> Dict[str, Any]:
        """
        Validation task with AI decision

        Args:
            generate_result: Output from generate task

        Returns:
            Validation result dict
        """
        logger.info(f"[VALIDATE] Validating: {generate_result}")

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

        logger.info(f"[VALIDATE] Decision: {ai_result.decision.value} (confidence: {ai_result.confidence:.2f})")
        logger.info(f"[VALIDATE] Reasoning: {ai_result.reasoning}")

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
            logger.info(f"[RETRY] Retry recommended (attempt {self.retry_count + 1}/{self.max_retries})")
            logger.info(f"[RETRY] Adjustments: {validate_result['adjustments']}")

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
            logger.warning(f"[RETRY] Asset flagged for human review")
            # In production, this would queue for human review
            # For now, continue with original asset
            return validate_result["asset_path"]

        else:
            # Approved or rejected - no retry
            logger.info(f"[RETRY] No retry needed: {decision.value}")
            return validate_result["asset_path"]

    def _optimize_task(self, validated_asset: Path) -> Path:
        """
        Optimization task (LOD generation, compression, etc.)

        In production, this would call:
            from forge_converter.optimization import optimize_asset
            optimized = optimize_asset(validated_asset, settings)
        """
        logger.info(f"[OPTIMIZE] Optimizing: {validated_asset}")

        # Use defined validated winners path
        output_path = self.get_path('validated', 'winners') / validated_asset.name

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

        logger.info(f"[OPTIMIZE] Optimized: {output_path}")
        return output_path

    def _export_task(self, engine: str, optimized_asset: Path) -> Path:
        """
        Export task for specific engine

        In production, this would call:
            from forge_converter import convert_for_engine
            exported = convert_for_engine(optimized_asset, engine)
        """
        logger.info(f"[EXPORT-{engine.upper()}] Exporting for {engine}")

        # Use defined engine-specific output path
        engine_dir = self.get_path('output', engine)

        # Determine proper file extension for each engine
        engine_extensions = {
            'unity': '.prefab',
            'unreal': '.uasset',
            'godot': '.tscn',
            'web': '.gltf',
            'blender': '.blend'
        }

        ext = engine_extensions.get(engine, f'.{engine}')
        output_path = engine_dir / f"{optimized_asset.stem}{ext}"

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

        logger.info(f"[EXPORT-{engine.upper()}] Exported: {output_path}")
        return output_path

    def _package_task(self, export_results: List[Path]) -> Path:
        """
        Package task (create deliverable package)

        In production, this would call:
            from forge_packaging import create_package
            package = create_package(export_results, metadata)
        """
        logger.info(f"[PACKAGE] Packaging {len(export_results)} exports")

        # Use defined packages path
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        package_name = f"package_{timestamp}_{id(self.current_job)}"
        package_path = self.get_path('packages', None) / package_name
        package_path.mkdir(parents=True, exist_ok=True)

        # In production: create actual package with metadata, README, etc.
        logger.info(f"[PACKAGE] Package created: {package_path}")
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
