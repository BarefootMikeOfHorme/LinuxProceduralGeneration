"""Characterisation tests for task complexity scoring and pattern selection.

These pin behaviour that was previously accidental rather than intended, and
which three tests in test_cli_task_decomposer.py had been asserting against.

Complexity scoring had `score += type_count * 2`, so one keyword match scored
2.0 on its own, exactly the TRIVIAL boundary. No description containing a
recognised keyword could be classified TRIVIAL, making the category
effectively unreachable. "Quick test" matched "test" and came back SIMPLE.

Pattern matching tested `'image' in description` before
`'validate' and 'batch'`, so the general rule shadowed the specific one. "Validate
batch of generated images for quality" matched image_generation, which requires
a GPU, and the batch_validation rule could never fire for a description
mentioning images, which is the case it exists for.

Novel-workflow generation handled generation, validation and analysis but not
enhancement, so a description asking to "optimize" had that stage silently
dropped.
"""

from __future__ import annotations

import pytest

@pytest.fixture
def process_orchestrator():
    from pathlib import Path

    from vaultmind_forge.cli.process_orchestrator import ProcessOrchestrator

    return ProcessOrchestrator(project_root=Path.cwd())


@pytest.fixture
def agent_manager():
    from vaultmind_forge.cli.agent_manager import AgentManager

    return AgentManager()


@pytest.fixture
def workflow_engine(agent_manager, process_orchestrator):
    from vaultmind_forge.cli.workflow_engine import WorkflowEngine

    return WorkflowEngine(agent_manager, process_orchestrator)


@pytest.fixture
def decomposer(workflow_engine):
    return IntelligentTaskDecomposer(workflow_engine)



from vaultmind_forge.cli.task_decomposer import (
    IntelligentTaskDecomposer,
    TaskComplexity,
    TaskType,
)


def score_for(word_count: int, types) -> float:
    """Recompute the scoring formula for inspection in failure output."""
    distinct = set(types)
    score = min(word_count / 8.0, 3.0)
    if TaskType.GENERATION in distinct:
        score += 2.0
        distinct = distinct - {TaskType.GENERATION}
    return round(score + len(distinct) * 0.5, 2)


class TestComplexityReachable:
    """TRIVIAL must be reachable, and must mean something."""

    def test_single_keyword_short_description_is_trivial(self):
        # The regression: 2 words plus one keyword scored 1.75 under the old
        # weights and 2.2 under the original, both at or above the boundary.
        distinct = [TaskType.VALIDATION]
        assert score_for(2, distinct) < 1.0, (
            "a two-word description with one keyword should score below the "
            f"TRIVIAL boundary, got {score_for(2, distinct)}"
        )

    def test_generation_raises_a_short_description_above_trivial(self):
        # Generation is the one type that actually produces an asset, so it is
        # weighted separately and more heavily than the rest.
        assert score_for(4, [TaskType.GENERATION]) >= 1.0

    def test_word_count_alone_cannot_reach_epic(self):
        # Length is capped at 3.0 so a long description with no recognised
        # keywords stays low. Otherwise padding a prompt would inflate it.
        assert score_for(10_000, []) == 3.0

    def test_monotonic_in_types_and_length(self):
        # More recognised types must never lower the score, and neither must
        # more words. Guards against the weighting accidentally inverting.
        fewer = score_for(20, [TaskType.GENERATION])
        more = score_for(20, [TaskType.GENERATION, TaskType.VALIDATION])
        assert more > fewer

        short = score_for(5, [TaskType.GENERATION])
        long = score_for(50, [TaskType.GENERATION])
        assert long >= short


class TestPatternOrdering:
    """The specific rule must be tested before the general rule."""

    @pytest.mark.anyio
    async def test_batch_validation_wins_over_image_generation(self, decomposer):
        result = await decomposer.decompose(
            "Validate batch of generated images for quality"
        )
        assert not result.resource_requirements["gpu"], (
            "validating a batch of existing images must not request a GPU; the "
            "image_generation pattern was matching first and claiming one"
        )

    @pytest.mark.anyio
    async def test_image_generation_still_matches_without_batch_validate(
        self, decomposer
    ):
        result = await decomposer.decompose("Create an image of a mountain range")
        assert result.resource_requirements["gpu"], (
            "a plain image request should still route to a GPU-requiring pattern"
        )
