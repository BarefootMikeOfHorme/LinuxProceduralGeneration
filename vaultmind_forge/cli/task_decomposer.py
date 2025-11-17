"""
Intelligent Task Decomposition Engine

Rembrandt-level sophistication:
- Context-aware task analysis
- Dependency inference from natural language
- Resource requirement prediction
- Optimal workflow generation
- Learning from execution history
- Adaptive complexity estimation
"""

from __future__ import annotations

import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from .workflow_engine import Workflow, Task, TaskType, WorkflowEngine
from .agent_manager import AgentType
from .terminal_ui import TerminalUI, console


class TaskComplexity(str, Enum):
    """Task complexity levels"""
    TRIVIAL = "trivial"      # <30s, single agent
    SIMPLE = "simple"         # <2min, 1-2 agents
    MODERATE = "moderate"     # <10min, 2-4 agents
    COMPLEX = "complex"       # <30min, 4-6 agents
    EPIC = "epic"            # >30min, 6+ agents, multi-stage


@dataclass
class TaskContext:
    """Rich context for task decomposition"""
    description: str
    keywords: List[str] = field(default_factory=list)
    requirements: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    complexity: TaskComplexity = TaskComplexity.MODERATE
    estimated_duration: float = 300.0  # seconds
    requires_gpu: bool = False
    requires_internet: bool = False


@dataclass
class DecompositionResult:
    """Result of task decomposition"""
    workflow: Workflow
    tasks: List[Task]
    estimated_duration: float
    required_agents: Set[AgentType]
    resource_requirements: Dict[str, Any]
    confidence: float  # 0.0-1.0, how confident we are in this decomposition
    reasoning: str  # Why we decomposed this way


class IntelligentTaskDecomposer:
    """
    AI-powered task decomposition engine

    Analyzes natural language descriptions and generates optimal workflows
    with:
    - Intelligent dependency inference
    - Resource-aware task planning
    - Agent capability matching
    - Adaptive complexity estimation
    - Historical learning
    """

    def __init__(self, workflow_engine: WorkflowEngine):
        self.workflow_engine = workflow_engine

        # Knowledge bases
        self.task_patterns = self._load_task_patterns()
        self.execution_history: List[Dict[str, Any]] = []

        # Keywords for task type inference
        self.generation_keywords = {
            'generate', 'create', 'produce', 'make', 'render', 'draw', 'paint',
            'synthesize', 'build', 'design', 'compose', 'craft'
        }

        self.validation_keywords = {
            'validate', 'verify', 'check', 'test', 'quality', 'review',
            'inspect', 'audit', 'assess', 'evaluate'
        }

        self.enhancement_keywords = {
            'enhance', 'improve', 'optimize', 'refine', 'polish', 'upgrade',
            'enrich', 'augment', 'boost', 'perfect'
        }

        self.analysis_keywords = {
            'analyze', 'examine', 'study', 'investigate', 'explore', 'research',
            'measure', 'profile', 'diagnose'
        }

    def _load_task_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        🔮 Ceremonial Task Patterns - Sacred Techniques

        These are Rembrandt's "techniques" - learned patterns that produce
        masterpiece workflows with real module execution paths.
        """
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent

        return {
            "image_generation": {
                "stages": ["enhance_prompt", "generate", "validate", "package"],
                "executors": {
                    "enhance_prompt": {
                        "type": TaskType.ENHANCEMENT,
                        "executor": "prompt_refiner",
                        "requires_agent": "prompt_refiner",
                    },
                    "generate": {
                        "type": TaskType.GENERATION,
                        "command": str(project_root / "vaultmind_cli.py"),
                        "executor": "python",
                        "params": {
                            "cli_command": "generate",
                            "default_width": 1024,
                            "default_height": 1024
                        },
                        "requires_gpu": True,
                        "estimated_duration": 60.0
                    },
                    "validate": {
                        "type": TaskType.VALIDATION,
                        "command": str(project_root / "vaultmind_forge" / "forge_validator" / "validator.py"),
                        "executor": "python",
                        "params": {
                            "backend": "basic"
                        },
                        "estimated_duration": 5.0
                    },
                    "package": {
                        "type": TaskType.PROCESSING,
                        "command": str(project_root / "vaultmind_forge" / "forge_packaging" / "packager.py"),
                        "executor": "python",
                        "estimated_duration": 3.0
                    }
                },
                "agents": [AgentType.PROMPT, AgentType.QUALITY],
                "requires_gpu": True,
                "complexity": TaskComplexity.MODERATE,
            },

            "character_creation": {
                "stages": ["concept", "prompt_design", "generate_variations", "select_best", "refine", "validate"],
                "executors": {
                    "concept": {
                        "type": TaskType.ANALYSIS,
                        "requires_agent": "style_profiler",
                        "estimated_duration": 10.0
                    },
                    "prompt_design": {
                        "type": TaskType.ENHANCEMENT,
                        "requires_agent": "prompt_refiner",
                        "estimated_duration": 15.0
                    },
                    "generate_variations": {
                        "type": TaskType.GENERATION,
                        "command": str(project_root / "vaultmind_cli.py"),
                        "executor": "python",
                        "params": {
                            "cli_command": "generate",
                            "batch": 5
                        },
                        "requires_gpu": True,
                        "estimated_duration": 180.0
                    },
                    "select_best": {
                        "type": TaskType.VALIDATION,
                        "requires_agent": "quality_guardian",
                        "estimated_duration": 10.0
                    },
                    "refine": {
                        "type": TaskType.ENHANCEMENT,
                        "command": str(project_root / "vaultmind_forge" / "forge_sr" / "upscaler.py"),
                        "executor": "python",
                        "requires_gpu": True,
                        "estimated_duration": 45.0
                    },
                    "validate": {
                        "type": TaskType.VALIDATION,
                        "command": str(project_root / "vaultmind_forge" / "forge_validator" / "validator.py"),
                        "executor": "python",
                        "estimated_duration": 5.0
                    }
                },
                "agents": [AgentType.PROMPT, AgentType.PARAMETER, AgentType.QUALITY, AgentType.MATERIAL],
                "requires_gpu": True,
                "complexity": TaskComplexity.COMPLEX,
            },

            "batch_validation": {
                "stages": ["collect_assets", "parallel_validate", "aggregate_results"],
                "executors": {
                    "collect_assets": {
                        "type": TaskType.PROCESSING,
                        "executor": "python",
                        "estimated_duration": 2.0
                    },
                    "parallel_validate": {
                        "type": TaskType.VALIDATION,
                        "command": str(project_root / "vaultmind_forge" / "forge_validator" / "validator.py"),
                        "executor": "python",
                        "params": {
                            "batch_mode": True
                        },
                        "estimated_duration": 15.0
                    },
                    "aggregate_results": {
                        "type": TaskType.ANALYSIS,
                        "executor": "python",
                        "estimated_duration": 1.0
                    }
                },
                "agents": [AgentType.QUALITY],
                "requires_gpu": False,
                "complexity": TaskComplexity.SIMPLE,
            },

            # 🔥 NEW: Multi-language terrain pipeline
            "terrain_generation": {
                "stages": ["rust_heightmap", "python_texture", "cpp_validate", "package"],
                "executors": {
                    "rust_heightmap": {
                        "type": TaskType.GENERATION,
                        "command": str(project_root / "target" / "release" / "terrain_gen"),
                        "executor": "rust",
                        "params": {
                            "resolution": 2048
                        },
                        "estimated_duration": 30.0
                    },
                    "python_texture": {
                        "type": TaskType.GENERATION,
                        "command": str(project_root / "vaultmind_cli.py"),
                        "executor": "python",
                        "params": {
                            "cli_command": "generate"
                        },
                        "requires_gpu": True,
                        "estimated_duration": 120.0
                    },
                    "cpp_validate": {
                        "type": TaskType.VALIDATION,
                        "command": str(project_root / "build" / "terrain_validator"),
                        "executor": "cpp",
                        "estimated_duration": 10.0
                    },
                    "package": {
                        "type": TaskType.PROCESSING,
                        "command": str(project_root / "vaultmind_forge" / "forge_packaging" / "packager.py"),
                        "executor": "python",
                        "estimated_duration": 5.0
                    }
                },
                "agents": [AgentType.PARAMETER],
                "requires_gpu": True,
                "complexity": TaskComplexity.EPIC,
            }
        }

    async def decompose(self, description: str, context: Optional[TaskContext] = None) -> DecompositionResult:
        """
        Decompose natural language task into optimized workflow

        This is where the MAGIC happens - Rembrandt analyzing the canvas
        before the first brushstroke.
        """
        # Build context if not provided
        if not context:
            context = await self._analyze_task_context(description)

        # Match to known patterns
        pattern = self._match_pattern(context)

        # Generate workflow
        if pattern:
            workflow = await self._generate_from_pattern(description, pattern, context)
            reasoning = f"Matched pattern '{pattern}' with {context.complexity.value} complexity"
        else:
            workflow = await self._generate_novel_workflow(description, context)
            reasoning = f"Generated novel workflow for {context.complexity.value} task"

        # Extract metadata
        tasks = list(workflow.tasks.values())
        required_agents = set()
        for task in tasks:
            if task.requires_agent:
                required_agents.add(AgentType(task.requires_agent))

        # Calculate confidence
        confidence = self._calculate_confidence(workflow, context, bool(pattern))

        return DecompositionResult(
            workflow=workflow,
            tasks=tasks,
            estimated_duration=workflow.estimate_duration(),
            required_agents=required_agents,
            resource_requirements={
                "gpu": any(t.requires_gpu for t in tasks),
                "agents": len(required_agents),
                "parallel_capacity": workflow.max_parallel,
            },
            confidence=confidence,
            reasoning=reasoning,
        )

    async def _analyze_task_context(self, description: str) -> TaskContext:
        """
        Analyze task description to extract context

        Rembrandt studying the subject before painting
        """
        description_lower = description.lower()
        words = set(re.findall(r'\b\w+\b', description_lower))

        # Extract keywords
        keywords = []
        task_types = []

        # Identify task types
        if words & self.generation_keywords:
            keywords.append("generation")
            task_types.append(TaskType.GENERATION)

        if words & self.validation_keywords:
            keywords.append("validation")
            task_types.append(TaskType.VALIDATION)

        if words & self.enhancement_keywords:
            keywords.append("enhancement")
            task_types.append(TaskType.ENHANCEMENT)

        if words & self.analysis_keywords:
            keywords.append("analysis")
            task_types.append(TaskType.ANALYSIS)

        # Detect requirements
        # GPU is needed for generation/rendering, but not validation/analysis
        requires_gpu = (
            any(word in description_lower for word in ['render', 'generate', 'sdxl', 'diffusion', 'create']) and
            not any(word in description_lower for word in ['validate', 'check', 'assess', 'analyze', 'inspect'])
        )
        requires_internet = any(word in description_lower for word in ['download', 'fetch', 'api', 'cloud'])

        # Estimate complexity
        complexity = self._estimate_complexity(description, task_types)

        # Estimate duration
        estimated_duration = self._estimate_duration(complexity, task_types)

        return TaskContext(
            description=description,
            keywords=keywords,
            complexity=complexity,
            estimated_duration=estimated_duration,
            requires_gpu=requires_gpu,
            requires_internet=requires_internet,
        )

    def _match_pattern(self, context: TaskContext) -> Optional[str]:
        """Match task to known pattern"""
        description_lower = context.description.lower()

        # Pattern matching rules (can be expanded)
        if 'image' in description_lower or 'picture' in description_lower:
            if 'character' in description_lower or 'person' in description_lower:
                return "character_creation"
            elif 'terrain' in description_lower or 'landscape' in description_lower:
                return "terrain_generation"
            else:
                return "image_generation"

        if 'validate' in description_lower and 'batch' in description_lower:
            return "batch_validation"

        return None

    async def _generate_from_pattern(
        self,
        description: str,
        pattern_name: str,
        context: TaskContext
    ) -> Workflow:
        """Generate workflow from known pattern"""
        pattern = self.task_patterns[pattern_name]

        workflow = self.workflow_engine.create_workflow(
            name=f"{pattern_name.replace('_', ' ').title()}",
            description=description,
            max_parallel=len(pattern["agents"]) + 1,
        )

        previous_task_id = None

        for i, stage_name in enumerate(pattern["stages"]):
            # Determine task type
            task_type = self._infer_task_type(stage_name)

            # Select agent
            agent = pattern["agents"][i % len(pattern["agents"])]

            # Create task
            task = self.workflow_engine.add_task_to_workflow(
                workflow_id=workflow.id,
                name=stage_name.replace('_', ' ').title(),
                task_type=task_type,
                executor=agent.value,
                depends_on=[previous_task_id] if previous_task_id else None,
                requires_gpu=pattern["requires_gpu"] and task_type == TaskType.GENERATION,
                requires_agent=agent.value,
                estimated_duration=context.estimated_duration / len(pattern["stages"]),
                priority=10 - i,  # Earlier stages have higher priority
            )

            previous_task_id = task.id

        return workflow

    async def _generate_novel_workflow(self, description: str, context: TaskContext) -> Workflow:
        """
        Generate workflow for novel/unknown task

        This is where Rembrandt becomes truly creative - handling the unknown
        """
        workflow = self.workflow_engine.create_workflow(
            name="Custom Workflow",
            description=description,
            max_parallel=4,
        )

        # Generate tasks based on keywords
        tasks_to_create = []

        if "generation" in context.keywords:
            tasks_to_create.extend([
                ("Enhance Prompt", TaskType.ENHANCEMENT, AgentType.PROMPT),
                ("Optimize Parameters", TaskType.ENHANCEMENT, AgentType.PARAMETER),
                ("Generate Content", TaskType.GENERATION, None),
            ])

        if "validation" in context.keywords:
            tasks_to_create.append(
                ("Validate Output", TaskType.VALIDATION, AgentType.QUALITY)
            )

        if "analysis" in context.keywords:
            tasks_to_create.append(
                ("Analyze Results", TaskType.ANALYSIS, AgentType.MATERIAL)
            )

        # Default to simple generation if no specific keywords
        if not tasks_to_create:
            tasks_to_create = [
                ("Prepare Task", TaskType.ENHANCEMENT, None),
                ("Execute Task", TaskType.GENERATION, None),
                ("Verify Results", TaskType.VALIDATION, None),
            ]

        # Create tasks with dependencies
        previous_task_id = None

        for i, (name, task_type, agent) in enumerate(tasks_to_create):
            task = self.workflow_engine.add_task_to_workflow(
                workflow_id=workflow.id,
                name=name,
                task_type=task_type,
                executor=agent.value if agent else None,
                depends_on=[previous_task_id] if previous_task_id else None,
                requires_gpu=task_type == TaskType.GENERATION and context.requires_gpu,
                requires_agent=agent.value if agent else None,
                estimated_duration=context.estimated_duration / len(tasks_to_create),
                priority=10 - i,
            )

            previous_task_id = task.id

        return workflow

    def _infer_task_type(self, stage_name: str) -> TaskType:
        """Infer task type from stage name"""
        stage_lower = stage_name.lower()

        if any(word in stage_lower for word in ['generate', 'create', 'produce', 'render']):
            return TaskType.GENERATION
        elif any(word in stage_lower for word in ['validate', 'verify', 'check', 'test']):
            return TaskType.VALIDATION
        elif any(word in stage_lower for word in ['enhance', 'optimize', 'refine', 'improve']):
            return TaskType.ENHANCEMENT
        elif any(word in stage_lower for word in ['analyze', 'examine', 'study']):
            return TaskType.ANALYSIS
        elif any(word in stage_lower for word in ['process', 'convert', 'export']):
            return TaskType.PROCESSING
        else:
            return TaskType.ORCHESTRATION

    def _estimate_complexity(self, description: str, task_types: List[TaskType]) -> TaskComplexity:
        """
        Estimate task complexity

        Rembrandt gauging how long this masterpiece will take
        """
        # Word count heuristic
        word_count = len(description.split())

        # Multiple task types = more complex
        type_count = len(set(task_types))

        # Calculate score
        score = 0
        score += min(word_count / 10, 3)  # Up to 3 points for description length
        score += type_count * 2  # 2 points per task type

        if score < 2:
            return TaskComplexity.TRIVIAL
        elif score < 4:
            return TaskComplexity.SIMPLE
        elif score < 7:
            return TaskComplexity.MODERATE
        elif score < 10:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.EPIC

    def _estimate_duration(self, complexity: TaskComplexity, task_types: List[TaskType]) -> float:
        """Estimate total duration in seconds"""
        base_durations = {
            TaskComplexity.TRIVIAL: 30,
            TaskComplexity.SIMPLE: 120,
            TaskComplexity.MODERATE: 600,
            TaskComplexity.COMPLEX: 1800,
            TaskComplexity.EPIC: 3600,
        }

        duration = base_durations[complexity]

        # Adjust for task types
        if TaskType.GENERATION in task_types:
            duration *= 1.5  # Generation is slower

        return duration

    def _calculate_confidence(self, workflow: Workflow, context: TaskContext, matched_pattern: bool) -> float:
        """
        Calculate confidence in decomposition

        Rembrandt's certainty in his composition
        """
        confidence = 0.5  # Base confidence

        # Pattern match boosts confidence
        if matched_pattern:
            confidence += 0.3

        # Valid DAG structure
        is_valid, _ = workflow.validate_dag()
        if is_valid:
            confidence += 0.1

        # Has enough tasks
        task_count = len(workflow.tasks)
        if 2 <= task_count <= 10:
            confidence += 0.1

        return min(confidence, 1.0)

    def visualize_decomposition(self, result: DecompositionResult) -> None:
        """Visualize decomposition result"""
        TerminalUI.clear()
        TerminalUI.header("Task Decomposition", result.workflow.name)

        console.print(f"[bold]Description:[/bold] {result.workflow.description}")
        console.print(f"[bold]Confidence:[/bold] {result.confidence * 100:.1f}%")
        console.print(f"[bold]Reasoning:[/bold] {result.reasoning}\n")

        console.print(f"[cyan]Tasks:[/cyan] {len(result.tasks)}")
        console.print(f"[cyan]Estimated Duration:[/cyan] {result.estimated_duration:.1f}s ({result.estimated_duration/60:.1f} min)")
        console.print(f"[cyan]Required Agents:[/cyan] {len(result.required_agents)}")
        console.print(f"[cyan]GPU Required:[/cyan] {'Yes' if result.resource_requirements['gpu'] else 'No'}\n")

        # Show workflow visualization
        self.workflow_engine.visualize_workflow(result.workflow.id)

    def learn_from_execution(self, workflow_id: str, actual_duration: float, success: bool) -> None:
        """
        Learn from workflow execution

        Rembrandt studying his finished work to improve the next
        """
        workflow = self.workflow_engine.workflows.get(workflow_id)
        if not workflow:
            return

        self.execution_history.append({
            "workflow_id": workflow_id,
            "estimated_duration": workflow.estimate_duration(),
            "actual_duration": actual_duration,
            "success": success,
            "task_count": len(workflow.tasks),
        })

        # TODO: Use history to improve future estimations (ML model)
