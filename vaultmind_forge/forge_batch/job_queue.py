"""
VaultMind Forge - Job Queue System
Priority-based queue for batch asset processing
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import heapq
import logging

logger = logging.getLogger(__name__)


class JobPriority(Enum):
    """Job priority levels"""
    URGENT = 90    # Critical production assets
    HIGH = 70      # Important assets needed soon
    NORMAL = 50    # Standard production queue
    LOW = 30       # Background work
    BATCH = 10     # Bulk generation, lowest priority


class JobStatus(Enum):
    """Job execution status"""
    PENDING = "pending"         # Submitted, waiting in queue
    BLOCKED = "blocked"         # Waiting for dependencies
    READY = "ready"             # Dependencies met, ready to run
    RUNNING = "running"         # Currently executing
    ERROR = "error"             # Failed, eligible for retry
    RETRY = "retry"             # Retrying after error
    COMPLETED = "completed"     # Finished successfully
    FAILED = "failed"           # Permanently failed
    CANCELLED = "cancelled"     # User cancelled


@dataclass
class BatchJob:
    """
    Batch processing job.

    Represents a single asset generation task with priority,
    dependencies, and execution tracking.
    """
    # Job identification
    id: str = field(default_factory=lambda: f"j_{uuid.uuid4().hex[:12]}")

    # Generation parameters
    prompt: str = ""
    output_type: str = "standard"
    target_engines: List[str] = field(default_factory=lambda: ["unity"])
    generation_params: Dict[str, Any] = field(default_factory=dict)

    # Job metadata
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.PENDING
    tags: Dict[str, str] = field(default_factory=dict)

    # Execution tracking
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # Results and errors
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Dependencies
    dependencies: List[str] = field(default_factory=list)

    # Special flags
    is_hero_asset: bool = False

    def __post_init__(self):
        """Initialize computed fields"""
        if not self.generation_params:
            self.generation_params = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BatchJob:
        """Create from dictionary"""
        # Convert enum values
        if 'priority' in data and isinstance(data['priority'], int):
            data['priority'] = JobPriority(data['priority'])
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = JobStatus(data['status'])

        return cls(**data)

    def is_ready_to_run(self, completed_jobs: set[str]) -> bool:
        """Check if job is ready to run (dependencies met)"""
        if self.status != JobStatus.PENDING:
            return False

        # Check if all dependencies are completed
        for dep_id in self.dependencies:
            if dep_id not in completed_jobs:
                return False

        return True

    def calculate_priority_score(self) -> int:
        """
        Calculate dynamic priority score.

        Factors:
        - Base priority
        - Age bonus (older jobs get priority boost)
        - Retry penalty
        - Hero asset bonus

        Returns:
            Priority score (0-100)
        """
        base_priority = self.priority.value

        # Age bonus: +1 point per hour, max +20
        created = datetime.fromisoformat(self.created_at)
        age_hours = (datetime.now() - created).total_seconds() / 3600
        age_bonus = min(int(age_hours), 20)

        # Retry penalty: -5 points per retry
        retry_penalty = self.retry_count * 5

        # Hero asset bonus: +10 points
        hero_bonus = 10 if self.is_hero_asset else 0

        score = base_priority + age_bonus - retry_penalty + hero_bonus
        return max(0, min(100, score))


class JobQueue:
    """
    Priority-based job queue with persistence.

    Features:
    - Priority-based ordering
    - FIFO within same priority
    - Job persistence (save/load)
    - Dependency tracking
    - Job filtering and search

    Example:
        >>> queue = JobQueue()
        >>> job = BatchJob(prompt="knight armor", priority=JobPriority.HIGH)
        >>> queue.submit(job)
        >>> next_job = queue.get_next_ready_job()
    """

    def __init__(self, persistence_path: Optional[Path] = None):
        """
        Initialize job queue.

        Args:
            persistence_path: Path to save queue state (default: None)
        """
        self.jobs: Dict[str, BatchJob] = {}
        self.completed_jobs: set[str] = set()
        self.persistence_path = persistence_path

        # Priority queue: (priority_score, job_id)
        # heapq is min-heap, so negate priority for max-heap behavior
        self._priority_queue: List[tuple[int, str]] = []

        if persistence_path and persistence_path.exists():
            self.load()

    # ========================================================================
    # Core Queue Operations
    # ========================================================================

    def submit(self, job: BatchJob) -> str:
        """
        Submit job to queue.

        Args:
            job: Job to submit

        Returns:
            Job ID
        """
        self.jobs[job.id] = job

        # Add to priority queue
        priority_score = -job.calculate_priority_score()  # Negate for max-heap
        heapq.heappush(self._priority_queue, (priority_score, job.id))

        logger.info(f"Job submitted: {job.id} (priority: {job.priority.name})")

        if self.persistence_path:
            self.save()

        return job.id

    def submit_batch(self, jobs: List[BatchJob]) -> List[str]:
        """
        Submit multiple jobs at once.

        Args:
            jobs: List of jobs to submit

        Returns:
            List of job IDs
        """
        job_ids = []
        for job in jobs:
            job_id = self.submit(job)
            job_ids.append(job_id)

        logger.info(f"Batch submitted: {len(jobs)} jobs")
        return job_ids

    def get_next_ready_job(self) -> Optional[BatchJob]:
        """
        Get highest priority job that's ready to run.

        Returns:
            Next ready job, or None if queue empty
        """
        # Rebuild priority queue with current scores
        self._rebuild_priority_queue()

        # Find first ready job
        while self._priority_queue:
            priority_score, job_id = heapq.heappop(self._priority_queue)

            if job_id not in self.jobs:
                continue  # Job was cancelled

            job = self.jobs[job_id]

            if job.is_ready_to_run(self.completed_jobs):
                # Don't change status here - will be changed when marked running
                # This prevents job from disappearing on next rebuild
                return job
            elif job.dependencies:
                # Put back in queue (blocked by dependencies)
                heapq.heappush(self._priority_queue, (priority_score, job_id))
                break

        return None

    def mark_running(self, job_id: str) -> None:
        """Mark job as running"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now().isoformat()

            if self.persistence_path:
                self.save()

    def mark_completed(self, job_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark job as completed.

        Args:
            job_id: Job ID
            result: Optional result data
        """
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now().isoformat()
            job.result = result

            self.completed_jobs.add(job_id)

            logger.info(f"Job completed: {job_id}")

            if self.persistence_path:
                self.save()

    def mark_failed(self, job_id: str, error: str, can_retry: bool = True) -> None:
        """
        Mark job as failed.

        Args:
            job_id: Job ID
            error: Error message
            can_retry: Whether job can be retried
        """
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.error = error

            if can_retry and job.retry_count < job.max_retries:
                job.status = JobStatus.RETRY
                job.retry_count += 1

                # Re-add to queue with lower priority
                priority_score = -job.calculate_priority_score()
                heapq.heappush(self._priority_queue, (priority_score, job_id))

                logger.warning(f"Job failed, will retry: {job_id} (attempt {job.retry_count}/{job.max_retries})")
            else:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now().isoformat()
                logger.error(f"Job permanently failed: {job_id}")

            if self.persistence_path:
                self.save()

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel job.

        Args:
            job_id: Job ID

        Returns:
            True if cancelled, False if not found
        """
        if job_id in self.jobs:
            job = self.jobs[job_id]

            if job.status in [JobStatus.RUNNING, JobStatus.COMPLETED, JobStatus.FAILED]:
                return False  # Can't cancel running/completed jobs

            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now().isoformat()

            logger.info(f"Job cancelled: {job_id}")

            if self.persistence_path:
                self.save()

            return True

        return False

    # ========================================================================
    # Query Operations
    # ========================================================================

    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job by ID"""
        return self.jobs.get(job_id)

    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        priority: Optional[JobPriority] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> List[BatchJob]:
        """
        List jobs with optional filters.

        Args:
            status: Filter by status
            priority: Filter by priority
            tags: Filter by tags (all must match)

        Returns:
            List of matching jobs
        """
        jobs = list(self.jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status]

        if priority:
            jobs = [j for j in jobs if j.priority == priority]

        if tags:
            jobs = [j for j in jobs if all(
                j.tags.get(k) == v for k, v in tags.items()
            )]

        return jobs

    def get_queue_depth(self) -> int:
        """Get number of pending jobs"""
        return len([j for j in self.jobs.values() if j.status == JobStatus.PENDING])

    def get_running_count(self) -> int:
        """Get number of running jobs"""
        return len([j for j in self.jobs.values() if j.status == JobStatus.RUNNING])

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        jobs = list(self.jobs.values())

        status_counts = {}
        for status in JobStatus:
            status_counts[status.value] = len([j for j in jobs if j.status == status])

        priority_counts = {}
        for priority in JobPriority:
            priority_counts[priority.name] = len([j for j in jobs if j.priority == priority])

        return {
            "total_jobs": len(jobs),
            "completed_jobs": len(self.completed_jobs),
            "queue_depth": self.get_queue_depth(),
            "running": self.get_running_count(),
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts
        }

    # ========================================================================
    # Persistence
    # ========================================================================

    def save(self) -> None:
        """Save queue state to disk"""
        if not self.persistence_path:
            return

        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "jobs": {job_id: job.to_dict() for job_id, job in self.jobs.items()},
            "completed_jobs": list(self.completed_jobs)
        }

        with open(self.persistence_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Queue saved to {self.persistence_path}")

    def load(self) -> None:
        """Load queue state from disk"""
        if not self.persistence_path or not self.persistence_path.exists():
            return

        try:
            with open(self.persistence_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Load jobs
            self.jobs = {}
            for job_id, job_data in data.get("jobs", {}).items():
                job = BatchJob.from_dict(job_data)
                self.jobs[job_id] = job

            # Load completed jobs
            self.completed_jobs = set(data.get("completed_jobs", []))

            # Rebuild priority queue
            self._rebuild_priority_queue()

            logger.info(f"Queue loaded from {self.persistence_path} ({len(self.jobs)} jobs)")

        except Exception as e:
            logger.error(f"Failed to load queue: {e}")

    def _rebuild_priority_queue(self) -> None:
        """Rebuild priority queue with current scores"""
        self._priority_queue = []

        for job_id, job in self.jobs.items():
            if job.status in [JobStatus.PENDING, JobStatus.BLOCKED, JobStatus.RETRY]:
                priority_score = -job.calculate_priority_score()
                heapq.heappush(self._priority_queue, (priority_score, job_id))

    def clear_completed(self) -> int:
        """
        Remove completed jobs from queue.

        Returns:
            Number of jobs removed
        """
        completed = [
            job_id for job_id, job in self.jobs.items()
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
        ]

        for job_id in completed:
            del self.jobs[job_id]

        logger.info(f"Cleared {len(completed)} completed jobs")

        if self.persistence_path:
            self.save()

        return len(completed)
