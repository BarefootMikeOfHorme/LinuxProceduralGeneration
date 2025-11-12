"""
Comprehensive tests for Checkpoint Manager

Testing checkpoint and recovery with Rembrandt-level sophistication
"""

import pytest
import asyncio
import tempfile
from pathlib import Path

from vaultmind_forge.cli.checkpoint_manager import (
    CheckpointManager,
    CheckpointType,
    RecoveryStrategy,
    CheckpointMetadata,
    CheckpointData,
)
from vaultmind_forge.cli.workflow_engine import Workflow, Task, TaskType, TaskStatus, WorkflowEngine
from vaultmind_forge.cli.agent_manager import AgentManager
from vaultmind_forge.cli.process_orchestrator import ProcessOrchestrator


@pytest.fixture
def temp_checkpoint_dir(tmp_path):
    """Create temporary checkpoint directory"""
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()
    return checkpoint_dir


@pytest.fixture
def checkpoint_manager(temp_checkpoint_dir):
    """Create checkpoint manager for testing"""
    return CheckpointManager(
        checkpoint_dir=temp_checkpoint_dir,
        auto_checkpoint_interval=10.0,
        max_checkpoints=20,
        compression_enabled=True,
    )


@pytest.fixture
def workflow_engine():
    """Create workflow engine for testing"""
    agent_manager = AgentManager()
    process_orchestrator = ProcessOrchestrator(project_root=Path.cwd())
    return WorkflowEngine(agent_manager, process_orchestrator)


@pytest.fixture
def sample_workflow(workflow_engine):
    """Create sample workflow for testing"""
    workflow = workflow_engine.create_workflow("Test Workflow", "Test description")

    # Add some tasks
    task1 = workflow_engine.add_task_to_workflow(
        workflow.id, "Task 1", TaskType.GENERATION, "test_executor"
    )
    task2 = workflow_engine.add_task_to_workflow(
        workflow.id, "Task 2", TaskType.VALIDATION, "test_executor"
    )

    return workflow


class TestCheckpointTypeEnum:
    """Test checkpoint type enumeration"""

    def test_checkpoint_type_values(self):
        """Test checkpoint type enum values"""
        assert CheckpointType.FULL.value == "full"
        assert CheckpointType.INCREMENTAL.value == "incremental"
        assert CheckpointType.MILESTONE.value == "milestone"
        assert CheckpointType.RECOVERY.value == "recovery"


class TestRecoveryStrategyEnum:
    """Test recovery strategy enumeration"""

    def test_recovery_strategy_values(self):
        """Test recovery strategy enum values"""
        assert RecoveryStrategy.RESUME.value == "resume"
        assert RecoveryStrategy.RETRY_FAILED.value == "retry_failed"
        assert RecoveryStrategy.RESTART.value == "restart"
        assert RecoveryStrategy.ROLLBACK.value == "rollback"


class TestCheckpointMetadata:
    """Test checkpoint metadata"""

    def test_create_metadata(self):
        """Test creating checkpoint metadata"""
        metadata = CheckpointMetadata(
            checkpoint_id="ckpt_test",
            workflow_id="wf_test",
            checkpoint_type=CheckpointType.FULL,
            timestamp=1234567890.0,
            version=1,
            total_tasks=5,
            completed_tasks=3,
            failed_tasks=0,
            running_tasks=2,
            compressed=True,
            size_bytes=1024,
            checksum="abc123",
        )

        assert metadata.checkpoint_id == "ckpt_test"
        assert metadata.workflow_id == "wf_test"
        assert metadata.checkpoint_type == CheckpointType.FULL
        assert metadata.total_tasks == 5
        assert metadata.completed_tasks == 3

    def test_metadata_to_dict(self):
        """Test converting metadata to dict"""
        metadata = CheckpointMetadata(
            checkpoint_id="ckpt_test",
            workflow_id="wf_test",
            checkpoint_type=CheckpointType.FULL,
            timestamp=1234567890.0,
            version=1,
            total_tasks=5,
            completed_tasks=3,
            failed_tasks=0,
            running_tasks=2,
            compressed=True,
            size_bytes=1024,
            checksum="abc123",
        )

        data = metadata.to_dict()

        assert isinstance(data, dict)
        assert data["checkpoint_id"] == "ckpt_test"
        assert data["total_tasks"] == 5

    def test_metadata_from_dict(self):
        """Test creating metadata from dict"""
        data = {
            "checkpoint_id": "ckpt_test",
            "workflow_id": "wf_test",
            "checkpoint_type": "full",
            "timestamp": 1234567890.0,
            "version": 1,
            "total_tasks": 5,
            "completed_tasks": 3,
            "failed_tasks": 0,
            "running_tasks": 2,
            "compressed": True,
            "size_bytes": 1024,
            "checksum": "abc123",
            "parent_checkpoint_id": None,
            "tags": [],
            "notes": "",
        }

        metadata = CheckpointMetadata.from_dict(data)

        assert metadata.checkpoint_id == "ckpt_test"
        assert metadata.total_tasks == 5

    def test_metadata_with_tags(self):
        """Test metadata with tags and notes"""
        metadata = CheckpointMetadata(
            checkpoint_id="ckpt_test",
            workflow_id="wf_test",
            checkpoint_type=CheckpointType.MILESTONE,
            timestamp=1234567890.0,
            version=1,
            total_tasks=5,
            completed_tasks=3,
            failed_tasks=0,
            running_tasks=2,
            compressed=True,
            size_bytes=1024,
            checksum="abc123",
            tags=["important", "before_major_change"],
            notes="Checkpoint before major refactoring",
        )

        assert "important" in metadata.tags
        assert metadata.notes == "Checkpoint before major refactoring"


class TestCheckpointManagerInitialization:
    """Test checkpoint manager initialization"""

    def test_create_checkpoint_manager(self, temp_checkpoint_dir):
        """Test creating checkpoint manager"""
        manager = CheckpointManager(checkpoint_dir=temp_checkpoint_dir)

        assert manager.checkpoint_dir == temp_checkpoint_dir
        assert manager.checkpoint_dir.exists()
        assert manager.auto_checkpoint_interval == 30.0
        assert manager.max_checkpoints == 50
        assert manager.compression_enabled

    def test_create_checkpoint_manager_custom_settings(self, temp_checkpoint_dir):
        """Test checkpoint manager with custom settings"""
        manager = CheckpointManager(
            checkpoint_dir=temp_checkpoint_dir,
            auto_checkpoint_interval=60.0,
            max_checkpoints=10,
            compression_enabled=False,
        )

        assert manager.auto_checkpoint_interval == 60.0
        assert manager.max_checkpoints == 10
        assert not manager.compression_enabled

    def test_checkpoint_directory_created(self, tmp_path):
        """Test checkpoint directory is created if missing"""
        checkpoint_dir = tmp_path / "new_checkpoints"
        assert not checkpoint_dir.exists()

        manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        assert checkpoint_dir.exists()


class TestCheckpointCreation:
    """Test checkpoint creation"""

    @pytest.mark.anyio
    async def test_create_full_checkpoint(self, checkpoint_manager, sample_workflow):
        """Test creating full checkpoint"""
        checkpoint_id = await checkpoint_manager.create_checkpoint(
            workflow=sample_workflow,
            checkpoint_type=CheckpointType.FULL,
        )

        assert checkpoint_id.startswith("ckpt_")
        assert checkpoint_id in checkpoint_manager.checkpoints

    @pytest.mark.anyio
    async def test_create_checkpoint_with_tags(self, checkpoint_manager, sample_workflow):
        """Test creating checkpoint with tags and notes"""
        checkpoint_id = await checkpoint_manager.create_checkpoint(
            workflow=sample_workflow,
            checkpoint_type=CheckpointType.MILESTONE,
            tags=["v1.0", "stable"],
            notes="Release checkpoint",
        )

        metadata = checkpoint_manager.checkpoints[checkpoint_id]
        assert "v1.0" in metadata.tags
        assert "stable" in metadata.tags
        assert metadata.notes == "Release checkpoint"

    @pytest.mark.anyio
    async def test_create_incremental_checkpoint(self, checkpoint_manager, sample_workflow):
        """Test creating incremental checkpoint"""
        # Create full checkpoint first
        full_id = await checkpoint_manager.create_checkpoint(
            workflow=sample_workflow,
            checkpoint_type=CheckpointType.FULL,
        )

        # Create incremental checkpoint
        incremental_id = await checkpoint_manager.create_checkpoint(
            workflow=sample_workflow,
            checkpoint_type=CheckpointType.INCREMENTAL,
        )

        incremental_meta = checkpoint_manager.checkpoints[incremental_id]
        assert incremental_meta.checkpoint_type == CheckpointType.INCREMENTAL
        assert incremental_meta.parent_checkpoint_id == full_id

    @pytest.mark.anyio
    async def test_checkpoint_versioning(self, checkpoint_manager, sample_workflow):
        """Test checkpoint version numbering"""
        # Create multiple checkpoints
        id1 = await checkpoint_manager.create_checkpoint(sample_workflow)
        id2 = await checkpoint_manager.create_checkpoint(sample_workflow)
        id3 = await checkpoint_manager.create_checkpoint(sample_workflow)

        # Check versions
        meta1 = checkpoint_manager.checkpoints[id1]
        meta2 = checkpoint_manager.checkpoints[id2]
        meta3 = checkpoint_manager.checkpoints[id3]

        assert meta1.version == 1
        assert meta2.version == 2
        assert meta3.version == 3


class TestCheckpointListing:
    """Test checkpoint listing and querying"""

    @pytest.mark.anyio
    async def test_list_all_checkpoints(self, checkpoint_manager, sample_workflow):
        """Test listing all checkpoints"""
        # Create some checkpoints
        await checkpoint_manager.create_checkpoint(sample_workflow)
        await checkpoint_manager.create_checkpoint(sample_workflow)

        checkpoints = checkpoint_manager.list_checkpoints()

        assert len(checkpoints) == 2

    @pytest.mark.anyio
    async def test_list_checkpoints_for_workflow(self, checkpoint_manager, workflow_engine, sample_workflow):
        """Test listing checkpoints for specific workflow"""
        # Create checkpoints for different workflows
        wf1 = sample_workflow
        wf2 = workflow_engine.create_workflow("Workflow 2", "Test")

        await checkpoint_manager.create_checkpoint(wf1)
        await checkpoint_manager.create_checkpoint(wf1)
        await checkpoint_manager.create_checkpoint(wf2)

        wf1_checkpoints = checkpoint_manager.list_checkpoints(workflow_id=wf1.id)

        assert len(wf1_checkpoints) == 2

    @pytest.mark.anyio
    async def test_get_latest_checkpoint(self, checkpoint_manager, sample_workflow):
        """Test getting latest checkpoint"""
        import anyio
        # Create multiple checkpoints
        await checkpoint_manager.create_checkpoint(sample_workflow)
        await anyio.sleep(0.01)  # Small delay to ensure different timestamps
        id2 = await checkpoint_manager.create_checkpoint(sample_workflow)
        await anyio.sleep(0.01)
        id3 = await checkpoint_manager.create_checkpoint(sample_workflow)

        latest = checkpoint_manager.get_latest_checkpoint(sample_workflow.id)

        assert latest is not None
        assert latest.checkpoint_id == id3


class TestCheckpointRestoration:
    """Test checkpoint restoration"""

    @pytest.mark.anyio
    async def test_restore_checkpoint(self, checkpoint_manager, sample_workflow):
        """Test restoring workflow from checkpoint"""
        # Create checkpoint
        checkpoint_id = await checkpoint_manager.create_checkpoint(sample_workflow)

        # Restore
        restored_workflow = await checkpoint_manager.restore_checkpoint(checkpoint_id)

        assert restored_workflow is not None
        assert restored_workflow.id == sample_workflow.id
        assert restored_workflow.name == sample_workflow.name

    @pytest.mark.anyio
    async def test_restore_nonexistent_checkpoint(self, checkpoint_manager):
        """Test restoring nonexistent checkpoint returns None"""
        restored = await checkpoint_manager.restore_checkpoint("invalid_id")

        assert restored is None


class TestCheckpointDeletion:
    """Test checkpoint deletion"""

    @pytest.mark.anyio
    async def test_delete_checkpoint(self, checkpoint_manager, sample_workflow):
        """Test deleting a checkpoint"""
        # Create checkpoint
        checkpoint_id = await checkpoint_manager.create_checkpoint(sample_workflow)

        assert checkpoint_id in checkpoint_manager.checkpoints

        # Delete
        success = await checkpoint_manager.delete_checkpoint(checkpoint_id)

        assert success
        assert checkpoint_id not in checkpoint_manager.checkpoints

    @pytest.mark.anyio
    async def test_cleanup_old_checkpoints(self, checkpoint_manager, sample_workflow):
        """Test automatic cleanup of old checkpoints"""
        import anyio
        # Create more checkpoints than max_checkpoints
        checkpoint_manager.max_checkpoints = 3

        checkpoint_ids = []
        for i in range(5):
            checkpoint_id = await checkpoint_manager.create_checkpoint(sample_workflow)
            checkpoint_ids.append(checkpoint_id)
            await anyio.sleep(0.01)

        # Trigger cleanup
        await checkpoint_manager._cleanup_old_checkpoints(sample_workflow.id)

        # Should only have max_checkpoints remaining
        remaining = checkpoint_manager.list_checkpoints(workflow_id=sample_workflow.id)
        assert len(remaining) <= checkpoint_manager.max_checkpoints


class TestCheckpointPersistence:
    """Test checkpoint persistence to disk"""

    @pytest.mark.anyio
    async def test_checkpoint_saved_to_disk(self, checkpoint_manager, sample_workflow):
        """Test checkpoint is saved to disk"""
        checkpoint_id = await checkpoint_manager.create_checkpoint(sample_workflow)

        # Check checkpoint file exists
        checkpoint_file = checkpoint_manager.checkpoint_dir / f"{checkpoint_id}.json.gz"
        assert checkpoint_file.exists() or (checkpoint_manager.checkpoint_dir / f"{checkpoint_id}.json").exists()

    @pytest.mark.anyio
    async def test_checkpoint_index_updated(self, checkpoint_manager, sample_workflow):
        """Test checkpoint index is updated"""
        await checkpoint_manager.create_checkpoint(sample_workflow)

        # Check index file exists
        index_file = checkpoint_manager.checkpoint_dir / "checkpoint_index.json"
        assert index_file.exists()

    @pytest.mark.anyio
    async def test_load_checkpoint_index_on_init(self, temp_checkpoint_dir, sample_workflow):
        """Test loading checkpoint index on initialization"""
        # Create manager and checkpoint
        manager1 = CheckpointManager(checkpoint_dir=temp_checkpoint_dir)
        checkpoint_id = await manager1.create_checkpoint(sample_workflow)

        # Create new manager (should load existing checkpoints)
        manager2 = CheckpointManager(checkpoint_dir=temp_checkpoint_dir)

        assert checkpoint_id in manager2.checkpoints


class TestCheckpointSerialization:
    """Test checkpoint serialization"""

    def test_serialize_workflow(self, checkpoint_manager, sample_workflow):
        """Test serializing workflow"""
        serialized = checkpoint_manager._serialize_workflow(sample_workflow)

        assert isinstance(serialized, dict)
        assert serialized["id"] == sample_workflow.id
        assert serialized["name"] == sample_workflow.name

    def test_serialize_task(self, checkpoint_manager, sample_workflow):
        """Test serializing task"""
        task = list(sample_workflow.tasks.values())[0]
        serialized = checkpoint_manager._serialize_task(task)

        assert isinstance(serialized, dict)
        assert serialized["id"] == task.id
        assert serialized["name"] == task.name


# Integration test
@pytest.mark.anyio
async def test_end_to_end_checkpoint_and_recovery():
    """Test complete checkpoint and recovery workflow"""
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_dir = Path(tmpdir) / "checkpoints"
        manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        # Create workflow
        agent_manager = AgentManager()
        process_orchestrator = ProcessOrchestrator(project_root=Path.cwd())
        workflow_engine = WorkflowEngine(agent_manager, process_orchestrator)

        workflow = workflow_engine.create_workflow("Test Workflow", "End-to-end test")
        task1 = workflow_engine.add_task_to_workflow(
            workflow.id, "Task 1", TaskType.GENERATION, "test"
        )
        task2 = workflow_engine.add_task_to_workflow(
            workflow.id, "Task 2", TaskType.VALIDATION, "test"
        )

        # Create checkpoint
        checkpoint_id = await manager.create_checkpoint(
            workflow,
            checkpoint_type=CheckpointType.MILESTONE,
            tags=["test", "integration"],
            notes="Integration test checkpoint",
        )

        assert checkpoint_id in manager.checkpoints

        # List checkpoints
        checkpoints = manager.list_checkpoints(workflow_id=workflow.id)
        assert len(checkpoints) == 1

        # Get metadata
        metadata = manager.checkpoints[checkpoint_id]
        assert metadata.workflow_id == workflow.id
        assert "test" in metadata.tags
        assert metadata.total_tasks == 2

        # Restore checkpoint
        restored = await manager.restore_checkpoint(checkpoint_id)
        assert restored is not None
        assert restored.id == workflow.id

        print(f"\n✅ End-to-end checkpoint test passed!")
        print(f"   Checkpoint ID: {checkpoint_id}")
        print(f"   Workflow: {workflow.name}")
        print(f"   Tasks: {len(workflow.tasks)}")
        print(f"   Version: {metadata.version}")
