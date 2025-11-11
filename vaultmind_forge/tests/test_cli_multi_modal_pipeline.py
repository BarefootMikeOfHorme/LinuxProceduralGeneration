"""
Comprehensive tests for Multi-Modal Pipeline Orchestrator

Testing cross-modal generation with Rembrandt-level sophistication
"""

import pytest
import asyncio
from pathlib import Path

from vaultmind_forge.cli.multi_modal_pipeline import (
    MultiModalPipeline,
    Modality,
    ModalQuality,
    ModalSpec,
    ModalResult,
    PipelineResult,
)
from vaultmind_forge.cli.workflow_engine import WorkflowEngine
from vaultmind_forge.cli.agent_manager import AgentManager
from vaultmind_forge.cli.process_orchestrator import ProcessOrchestrator


@pytest.fixture
def agent_manager():
    """Create agent manager for testing"""
    return AgentManager()


@pytest.fixture
def process_orchestrator():
    """Create process orchestrator for testing"""
    return ProcessOrchestrator(project_root=Path.cwd())


@pytest.fixture
def workflow_engine(agent_manager, process_orchestrator):
    """Create workflow engine for testing"""
    return WorkflowEngine(agent_manager, process_orchestrator)


@pytest.fixture
def pipeline(workflow_engine, agent_manager):
    """Create multi-modal pipeline for testing"""
    return MultiModalPipeline(workflow_engine, agent_manager)


class TestModalityEnums:
    """Test modality and quality enumerations"""

    def test_modality_values(self):
        """Test modality enum values"""
        assert Modality.IMAGE.value == "image"
        assert Modality.AUDIO.value == "audio"
        assert Modality.TEXT.value == "text"
        assert Modality.VIDEO.value == "video"
        assert Modality.MESH_3D.value == "mesh_3d"

    def test_modal_quality_values(self):
        """Test modal quality enum values"""
        assert ModalQuality.DRAFT.value == "draft"
        assert ModalQuality.STANDARD.value == "standard"
        assert ModalQuality.HIGH.value == "high"
        assert ModalQuality.MASTERPIECE.value == "masterpiece"


class TestModalSpec:
    """Test modal specification"""

    def test_create_basic_modal_spec(self):
        """Test creating basic modal spec"""
        spec = ModalSpec(
            modality=Modality.IMAGE,
            quality=ModalQuality.STANDARD,
        )

        assert spec.modality == Modality.IMAGE
        assert spec.quality == ModalQuality.STANDARD
        assert spec.params == {}
        assert spec.estimated_duration == 30.0
        assert not spec.requires_gpu
        assert spec.priority == 5

    def test_modal_spec_with_dependencies(self):
        """Test modal spec with dependencies"""
        spec = ModalSpec(
            modality=Modality.AUDIO,
            quality=ModalQuality.HIGH,
            depends_on_modalities=[Modality.TEXT, Modality.IMAGE],
            enhanced_by=[Modality.IMAGE],
        )

        assert Modality.TEXT in spec.depends_on_modalities
        assert Modality.IMAGE in spec.depends_on_modalities
        assert Modality.IMAGE in spec.enhanced_by

    def test_modal_spec_with_custom_params(self):
        """Test modal spec with custom parameters"""
        spec = ModalSpec(
            modality=Modality.IMAGE,
            quality=ModalQuality.MASTERPIECE,
            params={"width": 1024, "height": 1024, "steps": 50},
            estimated_duration=120.0,
            requires_gpu=True,
            priority=10,
        )

        assert spec.params["width"] == 1024
        assert spec.estimated_duration == 120.0
        assert spec.requires_gpu
        assert spec.priority == 10


class TestEnhancementRules:
    """Test cross-modal enhancement rules"""

    def test_enhancement_rules_structure(self, pipeline):
        """Test enhancement rules are properly structured"""
        rules = pipeline.enhancement_rules

        assert Modality.IMAGE in rules
        assert Modality.AUDIO in rules
        assert Modality.TEXT in rules

    def test_image_enhanced_by_text(self, pipeline):
        """Test image can be enhanced by text"""
        rules = pipeline.enhancement_rules[Modality.IMAGE]["enhanced_by"]

        assert Modality.TEXT in rules
        assert rules[Modality.TEXT]["type"] == "prompt_refinement"
        assert rules[Modality.TEXT]["weight"] == 0.8

    def test_image_enhanced_by_audio(self, pipeline):
        """Test image can be enhanced by audio"""
        rules = pipeline.enhancement_rules[Modality.IMAGE]["enhanced_by"]

        assert Modality.AUDIO in rules
        assert rules[Modality.AUDIO]["type"] == "mood_extraction"
        assert rules[Modality.AUDIO]["weight"] == 0.4

    def test_cross_modal_enhancement_bidirectional(self, pipeline):
        """Test enhancement works in both directions"""
        image_rules = pipeline.enhancement_rules[Modality.IMAGE]

        # Image enhanced by text
        assert Modality.TEXT in image_rules["enhanced_by"]

        # Image enhances text
        assert Modality.TEXT in image_rules["enhances"]


class TestQualityThresholds:
    """Test quality threshold configuration"""

    def test_quality_thresholds(self, pipeline):
        """Test quality thresholds are properly set"""
        thresholds = pipeline.quality_thresholds

        assert thresholds[ModalQuality.DRAFT] == 0.5
        assert thresholds[ModalQuality.STANDARD] == 0.7
        assert thresholds[ModalQuality.HIGH] == 0.85
        assert thresholds[ModalQuality.MASTERPIECE] == 0.95

    def test_quality_threshold_ordering(self, pipeline):
        """Test quality thresholds increase with quality level"""
        thresholds = pipeline.quality_thresholds

        assert thresholds[ModalQuality.DRAFT] < thresholds[ModalQuality.STANDARD]
        assert thresholds[ModalQuality.STANDARD] < thresholds[ModalQuality.HIGH]
        assert thresholds[ModalQuality.HIGH] < thresholds[ModalQuality.MASTERPIECE]


class TestPipelineCreation:
    """Test pipeline creation and validation"""

    @pytest.mark.anyio
    async def test_create_simple_pipeline(self, pipeline):
        """Test creating simple single-modality pipeline"""
        modalities = [
            ModalSpec(modality=Modality.IMAGE, quality=ModalQuality.STANDARD)
        ]

        pipeline_id = await pipeline.create_pipeline(
            name="Simple Image Gen",
            description="Generate a single image",
            modalities=modalities,
        )

        assert pipeline_id.startswith("mmp_")
        assert pipeline_id in pipeline.active_pipelines

    @pytest.mark.anyio
    async def test_create_multi_modal_pipeline(self, pipeline):
        """Test creating multi-modal pipeline"""
        modalities = [
            ModalSpec(modality=Modality.TEXT, quality=ModalQuality.STANDARD),
            ModalSpec(modality=Modality.IMAGE, quality=ModalQuality.HIGH),
            ModalSpec(modality=Modality.AUDIO, quality=ModalQuality.STANDARD),
        ]

        pipeline_id = await pipeline.create_pipeline(
            name="Multi-Modal Gen",
            description="Generate text, image, and audio",
            modalities=modalities,
            target_quality=ModalQuality.HIGH,
        )

        pipeline_state = pipeline.active_pipelines[pipeline_id]
        assert pipeline_state["name"] == "Multi-Modal Gen"
        assert pipeline_state["target_quality"] == ModalQuality.HIGH
        assert len(pipeline_state["modalities"]) == 3

    @pytest.mark.anyio
    async def test_create_pipeline_with_dependencies(self, pipeline):
        """Test creating pipeline with modal dependencies"""
        modalities = [
            ModalSpec(modality=Modality.TEXT, quality=ModalQuality.STANDARD),
            ModalSpec(
                modality=Modality.IMAGE,
                quality=ModalQuality.HIGH,
                depends_on_modalities=[Modality.TEXT],
            ),
        ]

        pipeline_id = await pipeline.create_pipeline(
            name="Dependent Pipeline",
            description="Image depends on text",
            modalities=modalities,
        )

        assert pipeline_id in pipeline.active_pipelines

    @pytest.mark.anyio
    async def test_validate_empty_modalities(self, pipeline):
        """Test validation rejects empty modalities"""
        with pytest.raises(ValueError, match="At least one modality required"):
            await pipeline.create_pipeline(
                name="Empty",
                description="No modalities",
                modalities=[],
            )

    @pytest.mark.anyio
    async def test_validate_missing_dependency(self, pipeline):
        """Test validation rejects missing dependencies"""
        modalities = [
            ModalSpec(
                modality=Modality.IMAGE,
                quality=ModalQuality.STANDARD,
                depends_on_modalities=[Modality.TEXT],  # TEXT not in pipeline
            ),
        ]

        with pytest.raises(ValueError, match="depends on .* which is not in pipeline"):
            await pipeline.create_pipeline(
                name="Invalid Deps",
                description="Missing dependency",
                modalities=modalities,
            )


class TestTopologicalSort:
    """Test topological sorting of modalities"""

    def test_topological_sort_no_dependencies(self, pipeline):
        """Test sorting modalities with no dependencies"""
        modalities = [
            ModalSpec(modality=Modality.IMAGE, quality=ModalQuality.STANDARD),
            ModalSpec(modality=Modality.AUDIO, quality=ModalQuality.STANDARD),
            ModalSpec(modality=Modality.TEXT, quality=ModalQuality.STANDARD),
        ]

        sorted_mods = pipeline._topological_sort_modalities(modalities)

        assert len(sorted_mods) == 3
        # Order doesn't matter when no dependencies

    def test_topological_sort_with_dependencies(self, pipeline):
        """Test sorting modalities with dependencies"""
        modalities = [
            ModalSpec(
                modality=Modality.IMAGE,
                quality=ModalQuality.STANDARD,
                depends_on_modalities=[Modality.TEXT],
            ),
            ModalSpec(modality=Modality.TEXT, quality=ModalQuality.STANDARD),
        ]

        sorted_mods = pipeline._topological_sort_modalities(modalities)

        # TEXT must come before IMAGE
        text_idx = next(i for i, s in enumerate(sorted_mods) if s.modality == Modality.TEXT)
        image_idx = next(i for i, s in enumerate(sorted_mods) if s.modality == Modality.IMAGE)
        assert text_idx < image_idx

    def test_topological_sort_circular_dependency(self, pipeline):
        """Test circular dependency detection"""
        modalities = [
            ModalSpec(
                modality=Modality.IMAGE,
                quality=ModalQuality.STANDARD,
                depends_on_modalities=[Modality.AUDIO],
            ),
            ModalSpec(
                modality=Modality.AUDIO,
                quality=ModalQuality.STANDARD,
                depends_on_modalities=[Modality.IMAGE],
            ),
        ]

        with pytest.raises(ValueError, match="Circular dependency"):
            pipeline._topological_sort_modalities(modalities)


class TestParallelGroups:
    """Test parallel execution group identification"""

    def test_parallel_groups_no_dependencies(self, pipeline):
        """Test all independent modalities in one group"""
        modalities = [
            ModalSpec(modality=Modality.IMAGE, quality=ModalQuality.STANDARD),
            ModalSpec(modality=Modality.AUDIO, quality=ModalQuality.STANDARD),
            ModalSpec(modality=Modality.TEXT, quality=ModalQuality.STANDARD),
        ]

        sorted_mods = pipeline._topological_sort_modalities(modalities)
        groups = pipeline._identify_parallel_groups(sorted_mods)

        # All should be in one group since no dependencies
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_parallel_groups_with_dependencies(self, pipeline):
        """Test dependent modalities in separate groups"""
        modalities = [
            ModalSpec(modality=Modality.TEXT, quality=ModalQuality.STANDARD),
            ModalSpec(
                modality=Modality.IMAGE,
                quality=ModalQuality.STANDARD,
                depends_on_modalities=[Modality.TEXT],
            ),
            ModalSpec(
                modality=Modality.AUDIO,
                quality=ModalQuality.STANDARD,
                depends_on_modalities=[Modality.TEXT],
            ),
        ]

        sorted_mods = pipeline._topological_sort_modalities(modalities)
        groups = pipeline._identify_parallel_groups(sorted_mods)

        # The algorithm creates a group for each modality with dependencies
        # TEXT should be in first group
        assert len(groups) >= 2
        assert groups[0][0].modality == Modality.TEXT
        # IMAGE and AUDIO depend on TEXT, so they come after
        assert all(spec.modality in [Modality.IMAGE, Modality.AUDIO] for group in groups[1:] for spec in group)


class TestExecutionPlan:
    """Test execution plan building"""

    def test_execution_plan_structure(self, pipeline):
        """Test execution plan contains required fields"""
        modalities = [
            ModalSpec(modality=Modality.IMAGE, quality=ModalQuality.STANDARD),
            ModalSpec(modality=Modality.TEXT, quality=ModalQuality.STANDARD),
        ]

        plan = pipeline._build_execution_plan(modalities)

        assert "sorted_modalities" in plan
        assert "execution_groups" in plan
        assert "critical_path_duration" in plan
        assert "parallelism_factor" in plan

    def test_execution_plan_critical_path(self, pipeline):
        """Test critical path duration calculation"""
        modalities = [
            ModalSpec(
                modality=Modality.TEXT,
                quality=ModalQuality.STANDARD,
                estimated_duration=10.0
            ),
            ModalSpec(
                modality=Modality.IMAGE,
                quality=ModalQuality.STANDARD,
                estimated_duration=30.0,
                depends_on_modalities=[Modality.TEXT],
            ),
        ]

        plan = pipeline._build_execution_plan(modalities)

        # Critical path: TEXT (10s) + IMAGE (30s) = 40s
        assert plan["critical_path_duration"] == 40.0

    def test_execution_plan_parallelism_factor(self, pipeline):
        """Test parallelism factor calculation"""
        modalities = [
            ModalSpec(modality=Modality.IMAGE, quality=ModalQuality.STANDARD),
            ModalSpec(modality=Modality.AUDIO, quality=ModalQuality.STANDARD),
            ModalSpec(modality=Modality.TEXT, quality=ModalQuality.STANDARD),
        ]

        plan = pipeline._build_execution_plan(modalities)

        # 3 modalities, 1 group = 3x parallelism
        assert plan["parallelism_factor"] == 3.0


class TestPipelineExecution:
    """Test pipeline execution"""

    @pytest.mark.anyio
    async def test_execute_simple_pipeline(self, pipeline):
        """Test executing simple single-modality pipeline"""
        modalities = [
            ModalSpec(modality=Modality.IMAGE, quality=ModalQuality.STANDARD)
        ]

        pipeline_id = await pipeline.create_pipeline(
            name="Simple",
            description="Test",
            modalities=modalities,
        )

        result = await pipeline.execute_pipeline(pipeline_id)

        assert isinstance(result, PipelineResult)
        assert result.pipeline_id == pipeline_id
        assert result.success
        assert Modality.IMAGE in result.modal_results

    @pytest.mark.anyio
    async def test_execute_multi_modal_pipeline(self, pipeline):
        """Test executing multi-modal pipeline"""
        modalities = [
            ModalSpec(modality=Modality.TEXT, quality=ModalQuality.STANDARD),
            ModalSpec(modality=Modality.IMAGE, quality=ModalQuality.STANDARD),
        ]

        pipeline_id = await pipeline.create_pipeline(
            name="Multi",
            description="Test",
            modalities=modalities,
        )

        result = await pipeline.execute_pipeline(pipeline_id)

        assert result.success
        assert len(result.modal_results) == 2
        assert Modality.TEXT in result.modal_results
        assert Modality.IMAGE in result.modal_results

    @pytest.mark.anyio
    async def test_execute_with_dependencies(self, pipeline):
        """Test executing pipeline with dependencies"""
        modalities = [
            ModalSpec(modality=Modality.TEXT, quality=ModalQuality.STANDARD),
            ModalSpec(
                modality=Modality.IMAGE,
                quality=ModalQuality.STANDARD,
                depends_on_modalities=[Modality.TEXT],
            ),
        ]

        pipeline_id = await pipeline.create_pipeline(
            name="Dependent",
            description="Test",
            modalities=modalities,
        )

        result = await pipeline.execute_pipeline(pipeline_id)

        assert result.success
        # Both modalities should complete
        assert len(result.modal_results) == 2

    @pytest.mark.anyio
    async def test_execute_nonexistent_pipeline(self, pipeline):
        """Test executing nonexistent pipeline raises error"""
        with pytest.raises(ValueError, match="Pipeline .* not found"):
            await pipeline.execute_pipeline("invalid_id")


class TestQualityCalculation:
    """Test quality calculation and refinement"""

    def test_calculate_overall_quality(self, pipeline):
        """Test overall quality calculation"""
        results = {
            Modality.IMAGE: ModalResult(
                modality=Modality.IMAGE,
                success=True,
                quality_score=0.8,
            ),
            Modality.TEXT: ModalResult(
                modality=Modality.TEXT,
                success=True,
                quality_score=0.9,
            ),
        }

        overall = pipeline._calculate_overall_quality(results)

        # Average of 0.8 and 0.9 = 0.85
        assert overall == pytest.approx(0.85)

    def test_calculate_overall_quality_empty(self, pipeline):
        """Test overall quality with no results"""
        overall = pipeline._calculate_overall_quality({})
        assert overall == 0.0

    def test_identify_refinement_targets(self, pipeline):
        """Test identifying modalities needing refinement"""
        results = {
            Modality.IMAGE: ModalResult(
                modality=Modality.IMAGE,
                success=True,
                quality_score=0.6,  # Below threshold
            ),
            Modality.TEXT: ModalResult(
                modality=Modality.TEXT,
                success=True,
                quality_score=0.9,  # Above threshold
            ),
        }

        targets = pipeline._identify_refinement_targets(results, 0.7)

        assert Modality.IMAGE in targets
        assert Modality.TEXT not in targets


class TestCrossModalConsistency:
    """Test cross-modal consistency validation"""

    def test_consistency_single_modality(self, pipeline):
        """Test consistency with single modality is always 1.0"""
        results = {
            Modality.IMAGE: ModalResult(
                modality=Modality.IMAGE,
                success=True,
                quality_score=0.8,
            ),
        }

        consistency = pipeline._validate_cross_modal_consistency(results)
        assert consistency == 1.0

    def test_consistency_multiple_modalities(self, pipeline):
        """Test consistency calculation across modalities"""
        results = {
            Modality.IMAGE: ModalResult(
                modality=Modality.IMAGE,
                success=True,
                quality_score=0.8,
            ),
            Modality.TEXT: ModalResult(
                modality=Modality.TEXT,
                success=True,
                quality_score=0.9,
            ),
        }

        consistency = pipeline._validate_cross_modal_consistency(results)

        # Should be between 0 and 1
        assert 0.0 <= consistency <= 1.0

    def test_calculate_modal_consistency(self, pipeline):
        """Test consistency calculation between two modalities"""
        result1 = ModalResult(
            modality=Modality.IMAGE,
            success=True,
            quality_score=0.8,
        )
        result2 = ModalResult(
            modality=Modality.TEXT,
            success=True,
            quality_score=0.9,
        )

        consistency = pipeline._calculate_modal_consistency(result1, result2)

        # Should be based on minimum quality
        assert 0.0 <= consistency <= 1.0


class TestEnhancementContext:
    """Test cross-modal enhancement context building"""

    def test_build_enhancement_context(self, pipeline):
        """Test building enhancement context for target modality"""
        existing_results = {
            Modality.TEXT: ModalResult(
                modality=Modality.TEXT,
                success=True,
                quality_score=0.9,
            ),
        }

        context = pipeline._build_enhancement_context(
            Modality.IMAGE,
            existing_results,
        )

        # IMAGE should be enhanced by TEXT
        assert "text" in context
        assert context["text"]["type"] == "prompt_refinement"
        assert context["text"]["weight"] == 0.8

    def test_build_enhancement_context_missing_source(self, pipeline):
        """Test enhancement context when source modality unavailable"""
        existing_results = {}

        context = pipeline._build_enhancement_context(
            Modality.IMAGE,
            existing_results,
        )

        # Should be empty since TEXT not available
        assert len(context) == 0


class TestVisualization:
    """Test pipeline visualization"""

    def test_visualize_pipeline(self, pipeline, capsys):
        """Test pipeline visualization output"""
        modalities = [
            ModalSpec(modality=Modality.IMAGE, quality=ModalQuality.STANDARD)
        ]

        async def create_and_visualize():
            pipeline_id = await pipeline.create_pipeline(
                name="Test",
                description="Test pipeline",
                modalities=modalities,
            )
            pipeline.visualize_pipeline(pipeline_id)

        asyncio.run(create_and_visualize())

    def test_visualize_nonexistent_pipeline(self, pipeline, capsys):
        """Test visualizing nonexistent pipeline"""
        pipeline.visualize_pipeline("invalid_id")
        # Should print error message, not raise


# Integration test
@pytest.mark.anyio
async def test_end_to_end_multi_modal_generation(agent_manager, process_orchestrator):
    """Test complete multi-modal generation workflow"""
    workflow_engine = WorkflowEngine(agent_manager, process_orchestrator)
    pipeline = MultiModalPipeline(workflow_engine, agent_manager)

    # Create complex multi-modal pipeline
    modalities = [
        ModalSpec(
            modality=Modality.TEXT,
            quality=ModalQuality.STANDARD,
            params={"prompt": "A serene mountain landscape"},
        ),
        ModalSpec(
            modality=Modality.IMAGE,
            quality=ModalQuality.HIGH,
            depends_on_modalities=[Modality.TEXT],
            requires_gpu=True,
        ),
        ModalSpec(
            modality=Modality.AUDIO,
            quality=ModalQuality.STANDARD,
            depends_on_modalities=[Modality.TEXT],
        ),
    ]

    pipeline_id = await pipeline.create_pipeline(
        name="Complete Multi-Modal",
        description="Generate text, image, and audio in harmony",
        modalities=modalities,
        target_quality=ModalQuality.STANDARD,
        max_refinement_iterations=2,
    )

    # Execute pipeline
    result = await pipeline.execute_pipeline(pipeline_id)

    # Verify result
    assert result.success
    assert len(result.modal_results) == 3
    assert result.overall_quality > 0.0
    assert result.consistency_score > 0.0
    assert result.total_duration > 0.0

    print(f"\n✅ End-to-end multi-modal pipeline test passed!")
    print(f"   Pipeline ID: {pipeline_id}")
    print(f"   Modalities: {len(result.modal_results)}")
    print(f"   Overall Quality: {result.overall_quality:.2%}")
    print(f"   Consistency: {result.consistency_score:.2%}")
    print(f"   Duration: {result.total_duration:.2f}s")
    print(f"   Refinements: {result.refinement_iterations}")
