"""
Comprehensive tests for Intelligent Task Decomposer

Testing the AI-powered task decomposition with Rembrandt-level precision
"""

import pytest
import asyncio
from pathlib import Path

from vaultmind_forge.cli.task_decomposer import (
    IntelligentTaskDecomposer,
    TaskContext,
    TaskComplexity,
    DecompositionResult,
)
from vaultmind_forge.cli.workflow_engine import WorkflowEngine, TaskType


@pytest.fixture
def agent_manager():
    """Create mock agent manager for testing"""
    from vaultmind_forge.cli.agent_manager import AgentManager
    return AgentManager()


@pytest.fixture
def process_orchestrator():
    """Create mock process orchestrator for testing"""
    from vaultmind_forge.cli.process_orchestrator import ProcessOrchestrator
    from pathlib import Path
    return ProcessOrchestrator(project_root=Path.cwd())


@pytest.fixture
def workflow_engine(agent_manager, process_orchestrator):
    """Create workflow engine for testing"""
    return WorkflowEngine(agent_manager, process_orchestrator)


@pytest.fixture
def decomposer(workflow_engine):
    """Create task decomposer for testing"""
    return IntelligentTaskDecomposer(workflow_engine)


class TestTaskContextAnalysis:
    """Test task context analysis and extraction"""

    @pytest.mark.anyio
    async def test_analyze_simple_generation_task(self, decomposer):
        """Test analysis of simple generation task"""
        description = "Generate an image of a sunset"
        context = await decomposer._analyze_task_context(description)

        assert context.description == description
        assert "generation" in context.keywords
        assert context.requires_gpu  # Image generation needs GPU
        assert context.complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]

    @pytest.mark.anyio
    async def test_analyze_complex_task(self, decomposer):
        """Test analysis of complex multi-step task"""
        description = "Generate a detailed character portrait, validate quality, enhance with post-processing, and analyze materials"
        context = await decomposer._analyze_task_context(description)

        assert "generation" in context.keywords
        assert "validation" in context.keywords
        assert "enhancement" in context.keywords
        assert "analysis" in context.keywords
        assert context.complexity in [TaskComplexity.COMPLEX, TaskComplexity.EPIC]

    @pytest.mark.anyio
    async def test_analyze_validation_task(self, decomposer):
        """Test analysis of validation-focused task"""
        description = "Validate and check the quality of generated images"
        context = await decomposer._analyze_task_context(description)

        assert "validation" in context.keywords
        assert not context.requires_gpu  # Validation doesn't need GPU

    @pytest.mark.anyio
    async def test_analyze_internet_requirement(self, decomposer):
        """Test detection of internet requirements"""
        description = "Download models from the cloud and fetch API data"
        context = await decomposer._analyze_task_context(description)

        assert context.requires_internet

    @pytest.mark.anyio
    async def test_complexity_estimation(self, decomposer):
        """Test complexity estimation for various task descriptions"""
        # Trivial task
        trivial = await decomposer._analyze_task_context("Quick test")
        assert trivial.complexity == TaskComplexity.TRIVIAL

        # Simple task
        simple = await decomposer._analyze_task_context("Generate a basic image")
        assert simple.complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]

        # Epic task
        epic = await decomposer._analyze_task_context(
            "Create a comprehensive game asset pipeline with terrain generation, "
            "character creation, material synthesis, quality validation, optimization, "
            "and export to multiple formats with detailed documentation"
        )
        assert epic.complexity in [TaskComplexity.COMPLEX, TaskComplexity.EPIC]


class TestPatternMatching:
    """Test pattern matching against known workflows"""

    def test_match_image_generation(self, decomposer):
        """Test matching image generation pattern"""
        context = TaskContext(
            description="Generate a beautiful scenic image",
            keywords=["generation"],
            complexity=TaskComplexity.MODERATE,
        )

        pattern = decomposer._match_pattern(context)
        assert pattern == "image_generation"

    def test_match_character_creation(self, decomposer):
        """Test matching character creation pattern"""
        context = TaskContext(
            description="Create a detailed character portrait image",
            keywords=["generation"],
            complexity=TaskComplexity.COMPLEX,
        )

        pattern = decomposer._match_pattern(context)
        assert pattern == "character_creation"

    def test_match_terrain_generation(self, decomposer):
        """Test matching terrain generation pattern"""
        context = TaskContext(
            description="Generate terrain image with mountains",
            keywords=["generation"],
            complexity=TaskComplexity.MODERATE,
        )

        pattern = decomposer._match_pattern(context)
        assert pattern == "terrain_generation"

    def test_match_batch_validation(self, decomposer):
        """Test matching batch validation pattern"""
        context = TaskContext(
            description="Validate batch of generated outputs",
            keywords=["validation"],
            complexity=TaskComplexity.SIMPLE,
        )

        pattern = decomposer._match_pattern(context)
        assert pattern == "batch_validation"

    def test_no_pattern_match(self, decomposer):
        """Test when no pattern matches"""
        context = TaskContext(
            description="Some unique task that doesn't match patterns",
            keywords=["analysis"],
            complexity=TaskComplexity.MODERATE,
        )

        pattern = decomposer._match_pattern(context)
        assert pattern is None


class TestWorkflowGeneration:
    """Test workflow generation from patterns and novel tasks"""

    @pytest.mark.anyio
    async def test_generate_from_image_pattern(self, decomposer):
        """Test workflow generation from image generation pattern"""
        context = TaskContext(
            description="Generate a sunset image",
            keywords=["generation"],
            complexity=TaskComplexity.MODERATE,
            requires_gpu=True,
        )

        workflow = await decomposer._generate_from_pattern(
            "Generate sunset",
            "image_generation",
            context
        )

        assert workflow is not None
        assert len(workflow.tasks) > 0
        assert "Image Generation" in workflow.name

        # Check stages are present
        task_names = [t.name.lower() for t in workflow.tasks.values()]
        assert any("prompt" in name for name in task_names)
        assert any("generate" in name or "param" in name for name in task_names)

    @pytest.mark.anyio
    async def test_generate_from_character_pattern(self, decomposer):
        """Test workflow generation from character creation pattern"""
        context = TaskContext(
            description="Create character",
            keywords=["generation"],
            complexity=TaskComplexity.COMPLEX,
            requires_gpu=True,
        )

        workflow = await decomposer._generate_from_pattern(
            "Create character",
            "character_creation",
            context
        )

        assert workflow is not None
        # Character creation should have more tasks
        assert len(workflow.tasks) >= 5

    @pytest.mark.anyio
    async def test_generate_novel_workflow(self, decomposer):
        """Test generation of novel workflow for unknown task"""
        context = TaskContext(
            description="Some unique task",
            keywords=["generation", "validation"],
            complexity=TaskComplexity.MODERATE,
            requires_gpu=True,
        )

        workflow = await decomposer._generate_novel_workflow(
            "Unique task",
            context
        )

        assert workflow is not None
        assert workflow.name == "Custom Workflow"
        assert len(workflow.tasks) > 0

        # Should have generation and validation tasks
        task_types = [t.type for t in workflow.tasks.values()]
        assert TaskType.GENERATION in task_types
        assert TaskType.VALIDATION in task_types


class TestFullDecomposition:
    """Test complete task decomposition pipeline"""

    @pytest.mark.anyio
    async def test_decompose_simple_task(self, decomposer):
        """Test decomposing a simple task"""
        result = await decomposer.decompose("Generate a simple test image")

        assert isinstance(result, DecompositionResult)
        assert result.workflow is not None
        assert len(result.tasks) > 0
        assert result.estimated_duration > 0
        assert result.confidence > 0.0 and result.confidence <= 1.0
        assert result.reasoning is not None

    @pytest.mark.anyio
    async def test_decompose_with_pattern_match(self, decomposer):
        """Test decomposition that matches a known pattern"""
        result = await decomposer.decompose("Generate a character portrait image")

        assert result.workflow is not None
        assert "character" in result.reasoning.lower()
        assert result.confidence >= 0.7  # Pattern match should have high confidence

        # Should require GPU
        assert result.resource_requirements["gpu"]

    @pytest.mark.anyio
    async def test_decompose_validation_task(self, decomposer):
        """Test decomposition of validation task"""
        result = await decomposer.decompose("Validate batch of generated images for quality")

        assert result.workflow is not None
        # Validation shouldn't require GPU
        assert not result.resource_requirements["gpu"]

    @pytest.mark.anyio
    async def test_decompose_with_custom_context(self, decomposer):
        """Test decomposition with provided context"""
        context = TaskContext(
            description="Custom task",
            complexity=TaskComplexity.EPIC,
            estimated_duration=3600.0,
            requires_gpu=True,
        )

        result = await decomposer.decompose("Custom task", context)

        assert result.estimated_duration >= 3600.0  # Should respect provided duration
        assert result.resource_requirements["gpu"]

    @pytest.mark.anyio
    async def test_decompose_complex_workflow(self, decomposer):
        """Test decomposition of complex multi-step workflow"""
        description = (
            "Generate terrain heightmap, create textures, "
            "add vegetation, validate quality, optimize, and export"
        )

        result = await decomposer.decompose(description)

        assert result.workflow is not None
        assert len(result.tasks) >= 5  # Should have multiple stages
        assert result.resource_requirements["agents"] > 0


class TestTaskTypeInference:
    """Test task type inference from stage names"""

    def test_infer_generation_type(self, decomposer):
        """Test inference of generation task type"""
        assert decomposer._infer_task_type("generate_image") == TaskType.GENERATION
        assert decomposer._infer_task_type("create_terrain") == TaskType.GENERATION
        assert decomposer._infer_task_type("produce_output") == TaskType.GENERATION

    def test_infer_validation_type(self, decomposer):
        """Test inference of validation task type"""
        assert decomposer._infer_task_type("validate_output") == TaskType.VALIDATION
        assert decomposer._infer_task_type("check_quality") == TaskType.VALIDATION
        assert decomposer._infer_task_type("verify_results") == TaskType.VALIDATION

    def test_infer_enhancement_type(self, decomposer):
        """Test inference of enhancement task type"""
        assert decomposer._infer_task_type("enhance_prompt") == TaskType.ENHANCEMENT
        assert decomposer._infer_task_type("optimize_params") == TaskType.ENHANCEMENT
        assert decomposer._infer_task_type("refine_output") == TaskType.ENHANCEMENT

    def test_infer_analysis_type(self, decomposer):
        """Test inference of analysis task type"""
        assert decomposer._infer_task_type("analyze_materials") == TaskType.ANALYSIS
        assert decomposer._infer_task_type("examine_results") == TaskType.ANALYSIS

    def test_infer_processing_type(self, decomposer):
        """Test inference of processing task type"""
        assert decomposer._infer_task_type("process_data") == TaskType.PROCESSING
        assert decomposer._infer_task_type("convert_format") == TaskType.PROCESSING
        assert decomposer._infer_task_type("export_output") == TaskType.PROCESSING


class TestConfidenceCalculation:
    """Test confidence scoring in decomposition"""

    def test_confidence_with_pattern_match(self, decomposer, workflow_engine):
        """Test confidence when pattern matches"""
        workflow = workflow_engine.create_workflow("Test", "Test workflow")
        workflow_engine.add_task_to_workflow(
            workflow.id,
            "Task 1",
            TaskType.GENERATION,
            "test_executor"
        )

        context = TaskContext(
            description="Test",
            complexity=TaskComplexity.MODERATE,
        )

        confidence = decomposer._calculate_confidence(workflow, context, matched_pattern=True)

        # Pattern match should boost confidence
        assert confidence >= 0.6

    def test_confidence_without_pattern_match(self, decomposer, workflow_engine):
        """Test confidence when no pattern matches"""
        workflow = workflow_engine.create_workflow("Test", "Test workflow")
        # Add at least one task to meet the "valid task count" condition
        workflow_engine.add_task_to_workflow(
            workflow.id,
            "Task 1",
            TaskType.GENERATION,
            "test_executor"
        )

        context = TaskContext(
            description="Test",
            complexity=TaskComplexity.MODERATE,
        )

        confidence = decomposer._calculate_confidence(workflow, context, matched_pattern=False)

        # No pattern match = lower confidence
        assert confidence < 1.0
        assert confidence > 0.0


class TestDurationEstimation:
    """Test duration estimation"""

    def test_trivial_duration(self, decomposer):
        """Test duration estimation for trivial tasks"""
        duration = decomposer._estimate_duration(TaskComplexity.TRIVIAL, [])
        assert duration == 30  # 30 seconds

    def test_epic_duration(self, decomposer):
        """Test duration estimation for epic tasks"""
        duration = decomposer._estimate_duration(TaskComplexity.EPIC, [])
        assert duration == 3600  # 1 hour

    def test_generation_duration_multiplier(self, decomposer):
        """Test that generation tasks take longer"""
        base_duration = decomposer._estimate_duration(TaskComplexity.MODERATE, [])
        generation_duration = decomposer._estimate_duration(
            TaskComplexity.MODERATE,
            [TaskType.GENERATION]
        )

        assert generation_duration > base_duration


class TestLearningSystem:
    """Test execution history learning"""

    def test_learn_from_execution(self, decomposer, workflow_engine):
        """Test learning from workflow execution"""
        workflow = workflow_engine.create_workflow("Test", "Test workflow")
        task = workflow_engine.add_task_to_workflow(
            workflow.id,
            "Task 1",
            TaskType.GENERATION,
            "test_executor"
        )

        # Record execution
        decomposer.learn_from_execution(
            workflow.id,
            actual_duration=45.0,
            success=True
        )

        assert len(decomposer.execution_history) == 1
        history = decomposer.execution_history[0]
        assert history["workflow_id"] == workflow.id
        assert history["actual_duration"] == 45.0
        assert history["success"] is True

    def test_multiple_execution_history(self, decomposer, workflow_engine):
        """Test accumulating execution history"""
        for i in range(5):
            workflow = workflow_engine.create_workflow(f"Test {i}", f"Test workflow {i}")

            decomposer.learn_from_execution(
                workflow.id,
                actual_duration=30.0 + i * 10,
                success=i % 2 == 0
            )

        assert len(decomposer.execution_history) == 5


class TestVisualization:
    """Test decomposition visualization"""

    def test_visualize_decomposition(self, decomposer, workflow_engine, capsys):
        """Test visualization output"""
        workflow = workflow_engine.create_workflow("Test", "Test workflow")
        task = workflow_engine.add_task_to_workflow(
            workflow.id,
            "Task 1",
            TaskType.GENERATION,
            "test_executor"
        )

        result = DecompositionResult(
            workflow=workflow,
            tasks=[task],
            estimated_duration=60.0,
            required_agents=set(),
            resource_requirements={"gpu": True, "agents": 1, "parallel_capacity": 4},
            confidence=0.85,
            reasoning="Test reasoning"
        )

        # Should not raise
        decomposer.visualize_decomposition(result)


# Integration test
@pytest.mark.anyio
async def test_end_to_end_decomposition(agent_manager, process_orchestrator):
    """Test complete end-to-end decomposition workflow"""
    workflow_engine = WorkflowEngine(agent_manager, process_orchestrator)
    decomposer = IntelligentTaskDecomposer(workflow_engine)

    # Decompose a realistic task
    result = await decomposer.decompose(
        "Generate a high-quality character portrait with validation and material analysis"
    )

    # Verify complete result
    assert result.workflow is not None
    assert result.workflow.id in workflow_engine.workflows
    assert len(result.tasks) >= 3
    assert result.estimated_duration > 0
    assert 0.0 < result.confidence <= 1.0
    assert result.reasoning is not None

    # Verify workflow is executable
    is_valid, error = result.workflow.validate_dag()
    assert is_valid, f"Generated workflow should be valid: {error}"

    print(f"\n[OK] End-to-end decomposition test passed!")
    print(f"   Workflow: {result.workflow.name}")
    print(f"   Tasks: {len(result.tasks)}")
    print(f"   Duration: {result.estimated_duration:.1f}s")
    print(f"   Confidence: {result.confidence:.2%}")
    print(f"   Reasoning: {result.reasoning}")
