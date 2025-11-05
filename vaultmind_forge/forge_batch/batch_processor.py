"""
VaultMind Forge - Batch Processor
Complete batch processing system with job queue, scheduling, and parallel execution
"""

from __future__ import annotations

import sys
import time
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
import logging

# Add modules to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from .job_queue import JobQueue, BatchJob, JobPriority, JobStatus
from .resource_manager import ResourceManager, ResourceRequirements
from forge_executor.pipeline import AssetPipeline, PipelineResult
from forge_converter.ai_control import AuthorityLevel

logger = logging.getLogger(__name__)


@dataclass
class WorkerStatus:
    """Worker status information"""
    worker_id: int
    is_active: bool
    current_job_id: Optional[str]
    jobs_completed: int
    jobs_failed: int
    allocated_resources: Dict[str, Any]


@dataclass
class BatchProgress:
    """Batch progress information"""
    total: int
    completed: int
    running: int
    pending: int
    failed: int
    percent: float


class BatchProcessor:
    """
    Complete batch processing system.

    Features:
    - Priority-based job queue
    - Resource-aware scheduling
    - Parallel pipeline execution
    - Progress tracking
    - Error recovery
    - Job persistence

    Example:
        >>> processor = BatchProcessor(max_workers=4)
        >>> job = BatchJob(prompt="knight armor", priority=JobPriority.HIGH)
        >>> job_id = processor.submit_job(job)
        >>> result = processor.wait_for_job(job_id)
    """

    def __init__(
        self,
        max_workers: int = 4,
        persistence_path: Optional[Path] = None,
        ai_authority: AuthorityLevel = AuthorityLevel.HIGH_AUTONOMY
    ):
        """
        Initialize batch processor.

        Args:
            max_workers: Maximum number of parallel workers
            persistence_path: Path for job queue persistence
            ai_authority: AI authority level for pipelines
        """
        self.max_workers = max_workers
        self.ai_authority = ai_authority

        # Core components
        self.queue = JobQueue(persistence_path)
        self.resource_manager = ResourceManager()

        # Worker management
        self.workers: Dict[int, threading.Thread] = {}
        self.worker_status: Dict[int, WorkerStatus] = {}
        self._next_worker_id = 0

        # Processing control
        self.running = False
        self._stop_event = threading.Event()
        self._scheduler_thread: Optional[threading.Thread] = None

        # Progress callbacks
        self.progress_callbacks: List[Callable[[str, float, str], None]] = []

        logger.info(f"BatchProcessor initialized (max_workers: {max_workers})")

    # ========================================================================
    # Job Submission
    # ========================================================================

    def submit_job(self, job: BatchJob) -> str:
        """
        Submit single job to queue.

        Args:
            job: Job to submit

        Returns:
            Job ID
        """
        job_id = self.queue.submit(job)

        # Start processing if not running
        if not self.running:
            self.start()

        return job_id

    def submit_batch(self, jobs: List[BatchJob]) -> List[str]:
        """
        Submit multiple jobs at once.

        Args:
            jobs: List of jobs to submit

        Returns:
            List of job IDs
        """
        job_ids = self.queue.submit_batch(jobs)

        # Start processing if not running
        if not self.running:
            self.start()

        return job_ids

    # ========================================================================
    # Processing Control
    # ========================================================================

    def start(self) -> None:
        """Start batch processing"""
        if self.running:
            return

        self.running = True
        self._stop_event.clear()

        # Start scheduler thread
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self._scheduler_thread.start()

        logger.info("Batch processor started")

    def stop(self, wait: bool = True) -> None:
        """
        Stop batch processing.

        Args:
            wait: Wait for current jobs to finish
        """
        if not self.running:
            return

        self.running = False
        self._stop_event.set()

        if wait:
            # Wait for workers to finish
            for worker_thread in self.workers.values():
                worker_thread.join(timeout=5.0)

        logger.info("Batch processor stopped")

    def _scheduler_loop(self) -> None:
        """Main scheduler loop"""
        while not self._stop_event.is_set():
            try:
                # Schedule next job if resources available
                self._schedule_next_job()

                # Clean up finished workers
                self._cleanup_workers()

                # Short sleep to avoid busy waiting
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)

    def _schedule_next_job(self) -> None:
        """Schedule next ready job"""
        # Check if we can start more workers
        active_workers = sum(1 for status in self.worker_status.values() if status.is_active)

        if active_workers >= self.max_workers:
            return

        # Get next ready job
        job = self.queue.get_next_ready_job()
        if not job:
            return

        # Estimate resources
        requirements = self.resource_manager.estimate_requirements(
            job.prompt,
            job.output_type,
            job.target_engines,
            job.generation_params
        )

        # Check if resources available
        if not self.resource_manager.can_allocate(requirements):
            logger.debug("Insufficient resources, waiting...")
            return

        # Allocate resources
        allocation = self.resource_manager.allocate_resources(requirements)
        if not allocation:
            return

        # Create worker
        worker_id = self._next_worker_id
        self._next_worker_id += 1

        self.worker_status[worker_id] = WorkerStatus(
            worker_id=worker_id,
            is_active=True,
            current_job_id=job.id,
            jobs_completed=0,
            jobs_failed=0,
            allocated_resources=allocation
        )

        # Start worker thread
        worker_thread = threading.Thread(
            target=self._worker_loop,
            args=(worker_id, job, allocation),
            daemon=True
        )
        self.workers[worker_id] = worker_thread
        worker_thread.start()

        logger.info(f"Worker {worker_id} started for job {job.id}")

    def _worker_loop(
        self,
        worker_id: int,
        job: BatchJob,
        allocation: Dict[str, Any]
    ) -> None:
        """Worker thread loop"""
        try:
            # Mark job as running
            self.queue.mark_running(job.id)

            # Create pipeline
            pipeline = AssetPipeline(
                ai_authority=self.ai_authority,
                max_retries=3,
                enable_lineage=True
            )

            # Setup GPU if allocated
            if 'gpu_id' in allocation:
                gpu_id = allocation['gpu_id']
                import os
                os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_id)

            # Execute pipeline
            self._emit_progress(job.id, 0.0, "Starting generation")

            result = pipeline.run_generation_pipeline(
                prompt=job.prompt,
                output_type=job.output_type,
                target_engines=job.target_engines,
                is_hero_asset=job.is_hero_asset,
                generation_params=job.generation_params
            )

            # Handle result
            if result.success:
                # Mark completed
                self.queue.mark_completed(job.id, result={
                    "outputs": {k: str(v) for k, v in result.outputs.items()},
                    "lineage_checksums": result.lineage_checksums,
                    "stages_completed": result.stages_completed
                })

                self.worker_status[worker_id].jobs_completed += 1
                self._emit_progress(job.id, 1.0, "Completed")

                logger.info(f"Job {job.id} completed successfully")

            else:
                # Mark failed
                error_msg = ", ".join(result.errors) if result.errors else "Unknown error"
                self.queue.mark_failed(job.id, error_msg, can_retry=True)

                self.worker_status[worker_id].jobs_failed += 1
                self._emit_progress(job.id, 0.0, f"Failed: {error_msg}")

                logger.error(f"Job {job.id} failed: {error_msg}")

        except Exception as e:
            # Mark failed
            self.queue.mark_failed(job.id, str(e), can_retry=True)
            self.worker_status[worker_id].jobs_failed += 1
            self._emit_progress(job.id, 0.0, f"Error: {e}")

            logger.error(f"Job {job.id} error: {e}", exc_info=True)

        finally:
            # Release resources
            self.resource_manager.release_resources(allocation)

            # Mark worker as inactive
            if worker_id in self.worker_status:
                self.worker_status[worker_id].is_active = False
                self.worker_status[worker_id].current_job_id = None

    def _cleanup_workers(self) -> None:
        """Clean up finished worker threads"""
        finished_workers = [
            worker_id for worker_id, thread in self.workers.items()
            if not thread.is_alive()
        ]

        for worker_id in finished_workers:
            del self.workers[worker_id]

    # ========================================================================
    # Progress Tracking
    # ========================================================================

    def add_progress_callback(
        self,
        callback: Callable[[str, float, str], None]
    ) -> None:
        """
        Add progress callback.

        Args:
            callback: Function(job_id, progress, message)
        """
        self.progress_callbacks.append(callback)

    def _emit_progress(self, job_id: str, progress: float, message: str) -> None:
        """Emit progress event to callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(job_id, progress, message)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    # ========================================================================
    # Query Operations
    # ========================================================================

    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status"""
        job = self.queue.get_job(job_id)
        return job.status if job else None

    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job by ID"""
        return self.queue.get_job(job_id)

    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        priority: Optional[JobPriority] = None
    ) -> List[BatchJob]:
        """List jobs with filters"""
        return self.queue.list_jobs(status=status, priority=priority)

    def get_batch_progress(self, job_ids: List[str]) -> BatchProgress:
        """
        Get progress for batch of jobs.

        Args:
            job_ids: List of job IDs

        Returns:
            BatchProgress object
        """
        jobs = [self.queue.get_job(job_id) for job_id in job_ids]
        jobs = [j for j in jobs if j]  # Filter None

        total = len(jobs)
        completed = len([j for j in jobs if j.status == JobStatus.COMPLETED])
        running = len([j for j in jobs if j.status == JobStatus.RUNNING])
        pending = len([j for j in jobs if j.status in [JobStatus.PENDING, JobStatus.READY]])
        failed = len([j for j in jobs if j.status == JobStatus.FAILED])

        percent = (completed / total * 100) if total > 0 else 0

        return BatchProgress(
            total=total,
            completed=completed,
            running=running,
            pending=pending,
            failed=failed,
            percent=percent
        )

    def is_batch_complete(self, job_ids: List[str]) -> bool:
        """Check if batch is complete"""
        progress = self.get_batch_progress(job_ids)
        return progress.completed + progress.failed == progress.total

    def wait_for_job(
        self,
        job_id: str,
        timeout: Optional[float] = None
    ) -> Optional[PipelineResult]:
        """
        Wait for job to complete.

        Args:
            job_id: Job ID
            timeout: Timeout in seconds (None = wait forever)

        Returns:
            PipelineResult or None if timeout/not found
        """
        start_time = time.time()

        while True:
            job = self.queue.get_job(job_id)
            if not job:
                return None

            if job.status == JobStatus.COMPLETED:
                # Convert result dict back to PipelineResult (simplified)
                return job.result

            if job.status in [JobStatus.FAILED, JobStatus.CANCELLED]:
                return None

            # Check timeout
            if timeout and (time.time() - start_time > timeout):
                return None

            time.sleep(1.0)

    def wait_for_batch(
        self,
        job_ids: List[str],
        timeout: Optional[float] = None
    ) -> bool:
        """
        Wait for entire batch to complete.

        Args:
            job_ids: List of job IDs
            timeout: Timeout in seconds

        Returns:
            True if all completed, False if timeout
        """
        start_time = time.time()

        while not self.is_batch_complete(job_ids):
            if timeout and (time.time() - start_time > timeout):
                return False

            time.sleep(1.0)

        return True

    # ========================================================================
    # Statistics and Monitoring
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        queue_stats = self.queue.get_stats()
        resources = self.resource_manager.get_system_resources()

        active_workers = sum(1 for s in self.worker_status.values() if s.is_active)
        total_completed = sum(s.jobs_completed for s in self.worker_status.values())
        total_failed = sum(s.jobs_failed for s in self.worker_status.values())

        return {
            "processor": {
                "running": self.running,
                "max_workers": self.max_workers,
                "active_workers": active_workers,
                "total_jobs_completed": total_completed,
                "total_jobs_failed": total_failed
            },
            "queue": queue_stats,
            "resources": {
                "cpu_percent": resources.cpu_percent,
                "ram_percent": resources.ram_percent,
                "disk_percent": resources.disk_percent,
                "gpu_count": len(resources.gpus)
            }
        }

    def get_worker_status(self) -> List[WorkerStatus]:
        """Get status of all workers"""
        return list(self.worker_status.values())

    def print_status(self) -> None:
        """Print current status (for CLI)"""
        stats = self.get_stats()

        print("\n=== Batch Processor Status ===")
        print(f"Running: {stats['processor']['running']}")
        print(f"Workers: {stats['processor']['active_workers']}/{stats['processor']['max_workers']} active")
        print(f"Completed: {stats['processor']['total_jobs_completed']}")
        print(f"Failed: {stats['processor']['total_jobs_failed']}")

        print(f"\n=== Queue ===")
        print(f"Total jobs: {stats['queue']['total_jobs']}")
        print(f"Queue depth: {stats['queue']['queue_depth']}")
        print(f"Running: {stats['queue']['running']}")

        print(f"\n=== Resources ===")
        print(f"CPU: {stats['resources']['cpu_percent']:.1f}%")
        print(f"RAM: {stats['resources']['ram_percent']:.1f}%")
        print(f"Disk: {stats['resources']['disk_percent']:.1f}%")
        print(f"GPUs: {stats['resources']['gpu_count']}")

    # ========================================================================
    # Job Control
    # ========================================================================

    def cancel_job(self, job_id: str) -> bool:
        """Cancel job"""
        return self.queue.cancel_job(job_id)

    def clear_completed(self) -> int:
        """Clear completed jobs from queue"""
        return self.queue.clear_completed()
