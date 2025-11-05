# VaultMind Forge - Batch Processing System Design

**Status**: Implementation Phase
**Date**: 2025-11-04
**Target**: Multi-asset job queue with priority scheduling and parallel execution

---

## Overview

The Batch Processing System enables efficient processing of multiple assets through the VaultMind Forge pipeline with:

- **Job Queue**: FIFO/Priority queue for asset generation jobs
- **Priority Scheduling**: Urgent jobs processed first
- **Resource Management**: GPU/CPU/Memory allocation and monitoring
- **Parallel Execution**: Multiple pipelines running concurrently
- **Progress Tracking**: Real-time status updates for all jobs
- **Error Recovery**: Automatic retry and error handling
- **Job Persistence**: Save/resume job queues

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Batch Processor                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Job Queue   │→ │  Scheduler   │→ │   Workers    │       │
│  │ (Priority)  │  │  (Resource   │  │  (Parallel   │       │
│  │             │  │   Aware)     │  │   Pipelines) │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
│         ↓                ↓                   ↓               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Resource Manager                          │    │
│  │  - GPU allocation                                   │    │
│  │  - CPU core assignment                              │    │
│  │  - Memory tracking                                  │    │
│  │  - Disk I/O monitoring                              │    │
│  └─────────────────────────────────────────────────────┘    │
│         ↓                ↓                   ↓               │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│  │Pipeline 1│   │Pipeline 2│   │Pipeline N│               │
│  └──────────┘   └──────────┘   └──────────┘               │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Job Queue

**Features**:
- Priority-based ordering (HIGH, NORMAL, LOW)
- FIFO within same priority
- Job persistence (save to disk)
- Job dependencies (job A must complete before job B)
- Batch job creation (submit 100 jobs at once)

**Job Structure**:
```python
@dataclass
class BatchJob:
    id: str
    prompt: str
    output_type: str
    target_engines: List[str]
    priority: JobPriority
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[PipelineResult]
    error: Optional[str]
    retry_count: int
    dependencies: List[str]  # Job IDs that must complete first
    tags: Dict[str, str]     # Metadata tags for filtering
```

**Queue Operations**:
- `submit_job()` - Add job to queue
- `submit_batch()` - Add multiple jobs
- `get_next_job()` - Get highest priority job ready to run
- `cancel_job()` - Remove job from queue
- `get_job_status()` - Query job status
- `list_jobs()` - List all jobs with filters

### 2. Scheduler

**Features**:
- Resource-aware scheduling (don't start job if GPU full)
- Priority-based assignment
- Fair scheduling (prevent starvation)
- Dependency resolution
- Time-based scheduling (run job at specific time)

**Scheduling Strategies**:
- **FIFO**: First in, first out
- **Priority**: High priority jobs first
- **Fair**: Round-robin across users/projects
- **Resource-Optimized**: Pack jobs to maximize GPU utilization

**Scheduler Logic**:
```python
def schedule_next_job():
    # Check available resources
    if not has_available_resources():
        return None

    # Get highest priority job that fits resources
    for job in queue.get_ready_jobs():
        required = estimate_resources(job)
        if can_allocate(required):
            return job

    return None
```

### 3. Resource Manager

**Features**:
- GPU allocation (which GPU for which job)
- CPU core assignment
- Memory limits (prevent OOM)
- Disk I/O throttling
- Resource usage monitoring

**Resource Types**:
```python
@dataclass
class ResourceRequirements:
    gpu_memory_gb: float = 8.0   # GPU VRAM needed
    cpu_cores: int = 4            # CPU cores needed
    ram_gb: float = 16.0          # System RAM needed
    disk_space_gb: float = 10.0   # Temp disk space needed
    max_duration_minutes: int = 60 # Timeout
```

**Resource Monitoring**:
- Track GPU utilization per job
- Detect GPU OOM and auto-retry with smaller batch
- Monitor CPU usage
- Track disk space usage

### 4. Worker Pool

**Features**:
- Parallel pipeline execution
- Configurable worker count
- Worker health monitoring
- Automatic worker restart on crash
- Worker isolation (separate processes)

**Worker Lifecycle**:
```
IDLE → ASSIGNED → RUNNING → COMPLETED → IDLE
  ↓                   ↓
  └─── ERROR ←────────┘
```

**Worker Management**:
- Dynamic worker count (scale up/down based on load)
- GPU affinity (worker locked to specific GPU)
- Worker reuse (don't recreate processes)

### 5. Progress Tracker

**Features**:
- Real-time progress updates
- Per-job progress (0-100%)
- Overall batch progress
- ETA calculation
- Progress callbacks

**Progress Events**:
- Job submitted
- Job started
- Job progress update (25%, 50%, 75%)
- Job completed
- Job failed
- Batch completed

---

## Job Lifecycle

```
PENDING → READY → RUNNING → COMPLETED
    ↓       ↓         ↓          ↓
    └─── BLOCKED    ERROR    SUCCESS
           ↓           ↓
        (waiting)   RETRY
```

**Status Descriptions**:
- **PENDING**: Job submitted, waiting in queue
- **BLOCKED**: Waiting for dependencies to complete
- **READY**: Dependencies met, ready to run
- **RUNNING**: Currently executing
- **ERROR**: Failed, eligible for retry
- **RETRY**: Retrying after error
- **COMPLETED**: Finished successfully or permanently failed
- **CANCELLED**: User cancelled

---

## Priority System

### Priority Levels

1. **URGENT** (90-100): Critical production assets
2. **HIGH** (70-89): Important assets needed soon
3. **NORMAL** (40-69): Standard production queue
4. **LOW** (10-39): Background/experimental work
5. **BATCH** (0-9): Bulk generation, lowest priority

### Priority Calculation

```python
def calculate_priority(job: BatchJob) -> int:
    base_priority = job.priority.value

    # Age bonus (older jobs get priority boost)
    age_hours = (datetime.now() - job.created_at).total_seconds() / 3600
    age_bonus = min(age_hours / 24 * 10, 20)  # Max +20 for jobs >2 days old

    # Retry penalty (retries get lower priority)
    retry_penalty = job.retry_count * 5

    # User priority multiplier (premium users)
    user_multiplier = get_user_priority_multiplier(job.user_id)

    final_priority = (base_priority + age_bonus - retry_penalty) * user_multiplier
    return int(np.clip(final_priority, 0, 100))
```

---

## Resource Management Strategy

### GPU Allocation

**Strategy 1: Exclusive GPU** (default)
- Each job gets full GPU
- No sharing between jobs
- Maximum performance per job
- Lower total throughput

**Strategy 2: Shared GPU**
- Multiple small jobs on one GPU
- Higher total throughput
- Risk of GPU memory conflicts
- Good for small assets

**GPU Selection**:
```python
def select_gpu(job: BatchJob) -> int:
    # Find GPU with most free memory
    gpus = get_gpu_status()

    required_mem = estimate_gpu_memory(job)

    for gpu_id, gpu in enumerate(gpus):
        if gpu.free_memory_gb >= required_mem:
            if gpu.current_jobs == 0:  # Prefer empty GPU
                return gpu_id

    # No empty GPU, find least loaded
    return min(enumerate(gpus), key=lambda x: x[1].current_jobs)[0]
```

### Memory Management

**Memory Limits**:
- Per-job memory limit (prevent OOM)
- System memory reserve (leave 20% for OS)
- Swap usage monitoring (alert if swapping)

**OOM Recovery**:
```python
def handle_oom_error(job: BatchJob):
    # Reduce batch size
    if job.generation_params.get("batch_size", 1) > 1:
        job.generation_params["batch_size"] //= 2
        return RetryDecision.RETRY

    # Reduce image resolution
    if job.generation_params.get("width", 512) > 256:
        job.generation_params["width"] //= 2
        job.generation_params["height"] //= 2
        return RetryDecision.RETRY

    # Give up
    return RetryDecision.FAIL
```

---

## Implementation Plan

### Phase 1: Core Queue System (2-3 hours)
- [ ] BatchJob dataclass
- [ ] JobQueue with priority
- [ ] Basic queue operations (submit, get, cancel)
- [ ] Job persistence (save/load from JSON)

### Phase 2: Scheduler (2-3 hours)
- [ ] Scheduler with resource awareness
- [ ] Priority calculation
- [ ] Dependency resolution
- [ ] Fair scheduling

### Phase 3: Resource Manager (2-3 hours)
- [ ] ResourceRequirements dataclass
- [ ] GPU status monitoring
- [ ] Resource allocation logic
- [ ] Memory tracking

### Phase 4: Worker Pool (2-3 hours)
- [ ] Worker class (wraps AssetPipeline)
- [ ] WorkerPool with parallel execution
- [ ] Worker health monitoring
- [ ] Error recovery

### Phase 5: Integration & Testing (1-2 hours)
- [ ] BatchProcessor main class
- [ ] Progress tracking
- [ ] Full integration test
- [ ] Performance benchmarks

**Total Estimated Time**: 9-14 hours

---

## Usage Examples

### Example 1: Submit Single Job

```python
from forge_batch import BatchProcessor, BatchJob, JobPriority

processor = BatchProcessor(max_workers=4)

job = BatchJob(
    prompt="medieval knight armor",
    output_type="character",
    target_engines=["unity", "unreal"],
    priority=JobPriority.NORMAL
)

job_id = processor.submit_job(job)
print(f"Job submitted: {job_id}")

# Wait for completion
result = processor.wait_for_job(job_id)
print(f"Job completed: {result.success}")
```

### Example 2: Submit Batch

```python
# Generate 100 character textures
jobs = []
for i in range(100):
    job = BatchJob(
        prompt=f"character texture variation {i}",
        output_type="texture",
        target_engines=["unity"],
        priority=JobPriority.BATCH
    )
    jobs.append(job)

# Submit all at once
job_ids = processor.submit_batch(jobs)
print(f"Submitted {len(job_ids)} jobs")

# Monitor progress
while not processor.is_batch_complete(job_ids):
    progress = processor.get_batch_progress(job_ids)
    print(f"Progress: {progress.completed}/{progress.total} ({progress.percent}%)")
    time.sleep(5)
```

### Example 3: Priority Job

```python
# Urgent production asset
urgent_job = BatchJob(
    prompt="hero character main protagonist",
    output_type="character",
    target_engines=["unity", "unreal", "godot"],
    priority=JobPriority.URGENT,
    is_hero_asset=True
)

job_id = processor.submit_job(urgent_job)

# This will jump to front of queue
processor.wait_for_job(job_id)
```

### Example 4: Dependent Jobs

```python
# Job A: Generate base texture
job_a = BatchJob(
    prompt="wood texture base",
    output_type="texture",
    priority=JobPriority.NORMAL
)
job_a_id = processor.submit_job(job_a)

# Job B: Generate variation (depends on A)
job_b = BatchJob(
    prompt="weathered wood texture",
    output_type="texture",
    priority=JobPriority.NORMAL,
    dependencies=[job_a_id]  # Won't start until A completes
)
job_b_id = processor.submit_job(job_b)
```

---

## Performance Targets

- **Throughput**: 100+ assets per hour (4 GPUs, 1-2 min per asset)
- **Queue Latency**: <1 second to submit job
- **Scheduling Overhead**: <100ms per scheduling decision
- **Worker Startup**: <5 seconds per worker
- **Resource Monitoring**: <1% CPU overhead

---

## Monitoring & Observability

### Metrics to Track

1. **Queue Metrics**:
   - Queue depth (jobs waiting)
   - Average wait time
   - Priority distribution

2. **Worker Metrics**:
   - Active workers
   - Worker utilization (% time busy)
   - Jobs per worker per hour

3. **Resource Metrics**:
   - GPU utilization (% used)
   - GPU memory usage
   - CPU utilization
   - Memory usage

4. **Job Metrics**:
   - Jobs per hour
   - Success rate
   - Average job duration
   - Retry rate

### Logging

```python
# Job lifecycle logging
[INFO] Job j_12345 submitted (priority: HIGH)
[INFO] Job j_12345 started on worker W1 (GPU 0)
[INFO] Job j_12345 progress: 25% (generation complete)
[INFO] Job j_12345 progress: 50% (validation complete)
[INFO] Job j_12345 progress: 75% (export complete)
[INFO] Job j_12345 completed successfully (duration: 2m 15s)

# Resource logging
[INFO] GPU 0: 75% utilized, 6.2GB/8GB memory
[INFO] Worker pool: 3/4 workers active
[INFO] Queue depth: 12 jobs (8 NORMAL, 3 LOW, 1 HIGH)
```

---

## Next Steps

After implementing the batch system:

1. **Web Dashboard** (Week 3): Real-time monitoring UI
2. **API Server** (Week 3): REST API for job submission
3. **Job Templates** (Week 3): Reusable job configurations
4. **Batch Analytics** (Week 4): Performance analysis and optimization

---

## Success Criteria

- [ ] Submit 100 jobs in <5 seconds
- [ ] Process 100+ assets per hour (4 GPU system)
- [ ] <5% job failure rate
- [ ] Automatic retry on transient failures
- [ ] Zero job loss (persistence works)
- [ ] Fair scheduling (no starvation)
- [ ] Resource utilization >80%
