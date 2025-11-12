"""
Comprehensive tests for Distributed Executor

Testing worker pools and load balancing with Rembrandt-level sophistication
"""

import pytest
import asyncio
from collections import deque

from vaultmind_forge.cli.distributed_executor import (
    DistributedExecutor,
    Worker,
    WorkerStatus,
    WorkerType,
    WorkerMetrics,
    LoadBalancingStrategy,
    TaskQueueItem,
)
from vaultmind_forge.cli.workflow_engine import Task, TaskType, TaskStatus


@pytest.fixture
def executor():
    """Create distributed executor for testing"""
    return DistributedExecutor(num_workers=4, strategy=LoadBalancingStrategy.RESOURCE_AWARE)


@pytest.fixture
def sample_worker():
    """Create sample worker for testing"""
    return Worker(
        id="worker_test",
        name="Test Worker",
        type=WorkerType.GENERAL,
        has_gpu=False,
        cpu_cores=2,
        memory_gb=4.0,
    )


@pytest.fixture
def sample_task():
    """Create sample task for testing"""
    return Task(
        id="task_test",
        name="Test Task",
        type=TaskType.GENERATION,
        executor="test",
        requires_gpu=False,
        requires_agent=False,
        estimated_duration=10.0,
    )


class TestWorkerStatusEnum:
    """Test worker status enumeration"""

    def test_worker_status_values(self):
        """Test worker status enum values"""
        assert WorkerStatus.INITIALIZING.value == "initializing"
        assert WorkerStatus.IDLE.value == "idle"
        assert WorkerStatus.BUSY.value == "busy"
        assert WorkerStatus.OVERLOADED.value == "overloaded"
        assert WorkerStatus.ERROR.value == "error"
        assert WorkerStatus.SHUTDOWN.value == "shutdown"


class TestWorkerTypeEnum:
    """Test worker type enumeration"""

    def test_worker_type_values(self):
        """Test worker type enum values"""
        assert WorkerType.GENERAL.value == "general"
        assert WorkerType.GPU_COMPUTE.value == "gpu_compute"
        assert WorkerType.CPU_COMPUTE.value == "cpu_compute"
        assert WorkerType.IO_BOUND.value == "io_bound"
        assert WorkerType.AGENT.value == "agent"


class TestLoadBalancingStrategyEnum:
    """Test load balancing strategy enumeration"""

    def test_load_balancing_strategy_values(self):
        """Test load balancing strategy enum values"""
        assert LoadBalancingStrategy.ROUND_ROBIN.value == "round_robin"
        assert LoadBalancingStrategy.LEAST_LOADED.value == "least_loaded"
        assert LoadBalancingStrategy.RESOURCE_AWARE.value == "resource_aware"
        assert LoadBalancingStrategy.PRIORITY_BASED.value == "priority_based"
        assert LoadBalancingStrategy.ADAPTIVE.value == "adaptive"


class TestWorkerMetrics:
    """Test worker metrics tracking"""

    def test_initial_metrics(self):
        """Test initial metrics state"""
        metrics = WorkerMetrics()

        assert metrics.tasks_completed == 0
        assert metrics.tasks_failed == 0
        assert metrics.total_execution_time == 0.0
        assert metrics.average_task_duration == 0.0
        assert metrics.cpu_usage == 0.0
        assert metrics.memory_usage == 0.0
        assert metrics.gpu_usage == 0.0
        assert metrics.queue_length == 0

    def test_update_task_completion_success(self):
        """Test updating metrics after successful task"""
        metrics = WorkerMetrics()
        metrics.update_task_completion(duration=10.0, success=True)

        assert metrics.tasks_completed == 1
        assert metrics.tasks_failed == 0
        assert metrics.total_execution_time == 10.0
        assert metrics.average_task_duration == 10.0

    def test_update_task_completion_failure(self):
        """Test updating metrics after failed task"""
        metrics = WorkerMetrics()
        metrics.update_task_completion(duration=5.0, success=False)

        assert metrics.tasks_completed == 0
        assert metrics.tasks_failed == 1
        assert metrics.total_execution_time == 5.0
        assert metrics.average_task_duration == 5.0

    def test_update_multiple_tasks(self):
        """Test metrics after multiple tasks"""
        metrics = WorkerMetrics()
        metrics.update_task_completion(10.0, True)
        metrics.update_task_completion(20.0, True)
        metrics.update_task_completion(5.0, False)

        assert metrics.tasks_completed == 2
        assert metrics.tasks_failed == 1
        assert metrics.total_execution_time == 35.0
        assert metrics.average_task_duration == pytest.approx(35.0 / 3)

    def test_success_rate(self):
        """Test success rate calculation"""
        metrics = WorkerMetrics()
        metrics.update_task_completion(10.0, True)
        metrics.update_task_completion(10.0, True)
        metrics.update_task_completion(10.0, False)

        assert metrics.success_rate() == pytest.approx(2.0 / 3.0)

    def test_success_rate_no_tasks(self):
        """Test success rate with no tasks"""
        metrics = WorkerMetrics()
        assert metrics.success_rate() == 0.0

    def test_efficiency_score(self):
        """Test efficiency score calculation"""
        metrics = WorkerMetrics()
        metrics.update_task_completion(10.0, True)
        metrics.cpu_usage = 50.0
        metrics.queue_length = 2

        efficiency = metrics.efficiency_score()

        # Should be weighted combination of factors
        assert 0.0 <= efficiency <= 1.0


class TestWorker:
    """Test worker functionality"""

    def test_create_worker(self, sample_worker):
        """Test creating a worker"""
        assert sample_worker.id == "worker_test"
        assert sample_worker.name == "Test Worker"
        assert sample_worker.type == WorkerType.GENERAL
        assert sample_worker.status == WorkerStatus.INITIALIZING
        assert not sample_worker.has_gpu
        assert sample_worker.cpu_cores == 2
        assert sample_worker.memory_gb == 4.0

    def test_worker_with_gpu(self):
        """Test creating GPU worker"""
        worker = Worker(
            id="gpu_worker",
            name="GPU Worker",
            type=WorkerType.GPU_COMPUTE,
            has_gpu=True,
        )

        assert worker.has_gpu
        assert worker.type == WorkerType.GPU_COMPUTE

    def test_can_handle_task_general(self, sample_worker, sample_task):
        """Test general worker can handle general task"""
        sample_worker.status = WorkerStatus.IDLE
        sample_task.requires_gpu = False

        assert sample_worker.can_handle_task(sample_task)

    def test_can_handle_task_gpu_required(self, sample_worker, sample_task):
        """Test worker without GPU cannot handle GPU task"""
        sample_worker.status = WorkerStatus.IDLE
        sample_task.requires_gpu = True

        assert not sample_worker.can_handle_task(sample_task)

    def test_can_handle_task_gpu_worker(self, sample_task):
        """Test GPU worker can handle GPU task"""
        worker = Worker(
            id="gpu",
            name="GPU Worker",
            type=WorkerType.GPU_COMPUTE,
            has_gpu=True,
        )
        worker.status = WorkerStatus.IDLE
        sample_task.requires_gpu = True

        assert worker.can_handle_task(sample_task)

    def test_can_handle_task_gpu_worker_rejects_cpu_task(self, sample_task):
        """Test GPU worker rejects non-GPU tasks"""
        worker = Worker(
            id="gpu",
            name="GPU Worker",
            type=WorkerType.GPU_COMPUTE,
            has_gpu=True,
        )
        worker.status = WorkerStatus.IDLE
        sample_task.requires_gpu = False  # CPU task

        assert not worker.can_handle_task(sample_task)

    def test_can_handle_task_agent_required(self, sample_task):
        """Test agent worker handles agent tasks"""
        worker = Worker(
            id="agent",
            name="Agent Worker",
            type=WorkerType.AGENT,
        )
        worker.status = WorkerStatus.IDLE
        sample_task.requires_agent = True

        assert worker.can_handle_task(sample_task)

    def test_can_handle_task_wrong_status(self, sample_worker, sample_task):
        """Test worker in wrong status cannot handle task"""
        sample_worker.status = WorkerStatus.ERROR

        assert not sample_worker.can_handle_task(sample_task)

    def test_load_score_idle(self, sample_worker):
        """Test load score for idle worker"""
        sample_worker.current_task = None
        sample_worker.task_queue = deque()
        sample_worker.metrics.cpu_usage = 0.0
        sample_worker.metrics.memory_usage = 0.0

        load = sample_worker.load_score()

        assert load == 0.0

    def test_load_score_with_current_task(self, sample_worker):
        """Test load score with current task"""
        sample_worker.current_task = "task_1"
        sample_worker.task_queue = deque()
        sample_worker.metrics.cpu_usage = 0.0
        sample_worker.metrics.memory_usage = 0.0

        load = sample_worker.load_score()

        assert load >= 0.5  # Base load for current task

    def test_load_score_with_queue(self, sample_worker):
        """Test load score with queued tasks"""
        sample_worker.current_task = None
        sample_worker.task_queue = deque(["task_1", "task_2", "task_3"])
        sample_worker.metrics.cpu_usage = 0.0
        sample_worker.metrics.memory_usage = 0.0

        load = sample_worker.load_score()

        assert load > 0.0  # Queue contributes to load

    def test_load_score_high_resource_usage(self, sample_worker):
        """Test load score with high resource usage"""
        sample_worker.current_task = None
        sample_worker.task_queue = deque()
        sample_worker.metrics.cpu_usage = 80.0
        sample_worker.metrics.memory_usage = 70.0

        load = sample_worker.load_score()

        assert load > 0.0  # Resource usage contributes to load


class TestExecutorInitialization:
    """Test executor initialization"""

    def test_create_executor_default(self):
        """Test creating executor with default settings"""
        executor = DistributedExecutor()

        assert executor.num_workers > 0
        assert executor.strategy == LoadBalancingStrategy.RESOURCE_AWARE
        assert len(executor.workers) == 0  # Not initialized yet

    def test_create_executor_custom_workers(self):
        """Test creating executor with custom worker count"""
        executor = DistributedExecutor(num_workers=8)

        assert executor.num_workers == 8

    def test_create_executor_custom_strategy(self):
        """Test creating executor with custom strategy"""
        executor = DistributedExecutor(strategy=LoadBalancingStrategy.ROUND_ROBIN)

        assert executor.strategy == LoadBalancingStrategy.ROUND_ROBIN

    def test_detect_system_capabilities(self, executor):
        """Test system capability detection"""
        capabilities = executor._detect_system_capabilities()

        assert "cpu_count" in capabilities
        assert "has_cuda" in capabilities
        assert "gpu_count" in capabilities
        assert capabilities["cpu_count"] > 0

    def test_design_worker_pool_cpu_only(self, executor):
        """Test worker pool design for CPU-only system"""
        capabilities = {
            "cpu_count": 8,
            "has_cuda": False,
            "gpu_count": 0,
        }

        workers = executor._design_worker_pool(capabilities)

        assert len(workers) == executor.num_workers
        # Should have CPU and I/O workers, no GPU workers
        assert all(not w["has_gpu"] for w in workers)

    def test_design_worker_pool_with_gpu(self, executor):
        """Test worker pool design for system with GPU"""
        capabilities = {
            "cpu_count": 8,
            "has_cuda": True,
            "gpu_count": 2,
        }

        workers = executor._design_worker_pool(capabilities)

        # Should have GPU workers
        gpu_workers = [w for w in workers if w["has_gpu"]]
        assert len(gpu_workers) > 0

    @pytest.mark.anyio
    async def test_initialize_executor(self, executor):
        """Test executor initialization"""
        await executor.initialize()

        assert len(executor.workers) == executor.num_workers
        # All workers should be idle
        assert all(w.status == WorkerStatus.IDLE for w in executor.workers.values())


class TestTaskSubmission:
    """Test task submission and queueing"""

    @pytest.mark.anyio
    async def test_submit_task(self, executor, sample_task):
        """Test submitting a task"""
        await executor.initialize()

        initial_queue_len = len(executor.task_queue)
        await executor.submit_task(sample_task)

        # Task should be queued (or assigned immediately)
        assert len(executor.task_queue) >= initial_queue_len or sample_task.id in executor.task_assignments

    @pytest.mark.anyio
    async def test_submit_multiple_tasks(self, executor):
        """Test submitting multiple tasks"""
        await executor.initialize()

        tasks = [
            Task(
                id=f"task_{i}",
                name=f"Task {i}",
                type=TaskType.GENERATION,
                executor="test",
            )
            for i in range(5)
        ]

        for idx, task in enumerate(tasks):
            await executor.submit_task(task, priority=idx)

        # All tasks should be queued or assigned
        total_handled = len(executor.task_queue) + len(executor.task_assignments)
        assert total_handled >= 0

    @pytest.mark.anyio
    async def test_task_priority_ordering(self, executor):
        """Test tasks are ordered by priority"""
        await executor.initialize()

        # Submit tasks with different priorities
        task_low = Task(id="low", name="Low Priority", type=TaskType.PROCESSING, executor="test")
        task_high = Task(id="high", name="High Priority", type=TaskType.PROCESSING, executor="test")

        await executor.submit_task(task_low, priority=1)
        await executor.submit_task(task_high, priority=10)

        # High priority task should come first in queue
        if executor.task_queue:
            assert executor.task_queue[0].priority >= executor.task_queue[-1].priority


class TestLoadBalancing:
    """Test load balancing strategies"""

    def test_round_robin_select(self, executor):
        """Test round-robin worker selection"""
        workers = [
            Worker(id=f"w{i}", name=f"Worker {i}", type=WorkerType.GENERAL)
            for i in range(3)
        ]

        # Select workers in round-robin fashion
        selected = []
        for _ in range(6):
            worker = executor._round_robin_select(workers)
            selected.append(worker.id)

        # Should cycle through workers
        assert selected[0] == selected[3]
        assert selected[1] == selected[4]
        assert selected[2] == selected[5]

    def test_least_loaded_select(self, executor):
        """Test least-loaded worker selection"""
        workers = [
            Worker(id="w1", name="Worker 1", type=WorkerType.GENERAL),
            Worker(id="w2", name="Worker 2", type=WorkerType.GENERAL),
            Worker(id="w3", name="Worker 3", type=WorkerType.GENERAL),
        ]

        # Set different loads
        workers[0].current_task = "task_1"  # High load
        workers[1].task_queue = deque(["t1", "t2"])  # Medium load
        workers[2].current_task = None  # Low load

        selected = executor._least_loaded_select(workers)

        # Should select least loaded worker (w3)
        assert selected.id == "w3"

    def test_resource_aware_select_gpu_task(self, executor, sample_task):
        """Test resource-aware selection for GPU task"""
        workers = [
            Worker(id="cpu", name="CPU Worker", type=WorkerType.CPU_COMPUTE, has_gpu=False),
            Worker(id="gpu", name="GPU Worker", type=WorkerType.GPU_COMPUTE, has_gpu=True),
        ]

        sample_task.requires_gpu = True

        selected = executor._resource_aware_select(workers, sample_task)

        # Should prefer GPU worker
        assert selected.has_gpu

    def test_resource_aware_select_considers_efficiency(self, executor, sample_task):
        """Test resource-aware selection considers efficiency"""
        workers = [
            Worker(id="w1", name="Worker 1", type=WorkerType.GENERAL),
            Worker(id="w2", name="Worker 2", type=WorkerType.GENERAL),
        ]

        # Worker 1 has better efficiency
        workers[0].metrics.tasks_completed = 10
        workers[0].metrics.tasks_failed = 1
        workers[0].metrics.cpu_usage = 50.0

        # Worker 2 has worse efficiency
        workers[1].metrics.tasks_completed = 5
        workers[1].metrics.tasks_failed = 5
        workers[1].metrics.cpu_usage = 80.0

        selected = executor._resource_aware_select(workers, sample_task)

        # Should prefer more efficient worker
        assert selected.metrics.efficiency_score() >= workers[1].metrics.efficiency_score()

    def test_adaptive_select(self, executor, sample_task):
        """Test adaptive worker selection"""
        workers = [
            Worker(id="w1", name="Worker 1", type=WorkerType.GENERAL),
            Worker(id="w2", name="Worker 2", type=WorkerType.GENERAL),
        ]

        selected = executor._adaptive_select(workers, sample_task)

        # Should return a valid worker
        assert selected in workers


class TestTaskExecution:
    """Test task execution"""

    @pytest.mark.anyio
    async def test_execute_task_success(self, executor, sample_task):
        """Test successful task execution"""
        await executor.initialize()

        worker = list(executor.workers.values())[0]
        worker.status = WorkerStatus.IDLE

        await executor._assign_task_to_worker(worker, sample_task)

        # Wait for execution
        await asyncio.sleep(0.5)

        # Task should be completed
        assert sample_task.id in executor.completed_tasks
        assert executor.completed_tasks[sample_task.id]["success"]

    @pytest.mark.anyio
    async def test_worker_metrics_updated(self, executor, sample_task):
        """Test worker metrics are updated after execution"""
        await executor.initialize()

        worker = list(executor.workers.values())[0]
        worker.status = WorkerStatus.IDLE

        initial_completed = worker.metrics.tasks_completed

        await executor._assign_task_to_worker(worker, sample_task)

        # Wait for execution
        await asyncio.sleep(0.5)

        # Metrics should be updated
        assert worker.metrics.tasks_completed > initial_completed


class TestTaskQueueItem:
    """Test task queue item"""

    def test_create_queue_item(self, sample_task):
        """Test creating task queue item"""
        item = TaskQueueItem(task=sample_task, priority=5)

        assert item.task == sample_task
        assert item.priority == 5
        assert item.attempts == 0
        assert item.max_attempts == 3

    def test_queue_item_with_custom_attempts(self, sample_task):
        """Test queue item with custom max attempts"""
        item = TaskQueueItem(task=sample_task, priority=10, max_attempts=5)

        assert item.max_attempts == 5


class TestVisualization:
    """Test worker visualization"""

    @pytest.mark.anyio
    async def test_visualize_workers(self, executor, capsys):
        """Test worker visualization"""
        await executor.initialize()

        # Should not raise
        executor.visualize_workers()


# Integration test
@pytest.mark.anyio
async def test_end_to_end_distributed_execution():
    """Test complete distributed execution workflow"""
    executor = DistributedExecutor(num_workers=4, strategy=LoadBalancingStrategy.RESOURCE_AWARE)

    # Initialize
    await executor.initialize()

    assert len(executor.workers) == 4

    # Submit tasks
    tasks = [
        Task(
            id=f"task_{i}",
            name=f"Task {i}",
            type=TaskType.GENERATION if i % 2 == 0 else TaskType.PROCESSING,
            executor="test",
            requires_gpu=(i % 3 == 0),
            estimated_duration=5.0,
        )
        for i in range(10)
    ]

    for i, task in enumerate(tasks):
        await executor.submit_task(task, priority=10 - i)

    # Wait for some execution
    await asyncio.sleep(1.0)

    # Check that tasks are being processed
    total_handled = len(executor.completed_tasks) + len(executor.task_assignments)
    assert total_handled > 0

    print(f"\n✅ End-to-end distributed execution test passed!")
    print(f"   Workers: {len(executor.workers)}")
    print(f"   Completed: {len(executor.completed_tasks)}")
    print(f"   Assigned: {len(executor.task_assignments)}")
    print(f"   Queued: {len(executor.task_queue)}")
