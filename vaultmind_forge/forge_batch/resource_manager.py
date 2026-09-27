"""
VaultMind Forge - Resource Manager
GPU/CPU/Memory allocation and monitoring for batch processing
"""

from __future__ import annotations

import psutil
import platform
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


@dataclass
class ResourceRequirements:
    """
    Resource requirements for a job.

    Default values are for typical diffusion generation job.
    """

    gpu_memory_gb: float = 8.0  # GPU VRAM needed
    cpu_cores: int = 4  # CPU cores needed
    ram_gb: float = 16.0  # System RAM needed
    disk_space_gb: float = 10.0  # Temp disk space needed
    max_duration_minutes: int = 60  # Timeout


@dataclass
class GPUStatus:
    """GPU status information"""

    gpu_id: int
    name: str
    total_memory_gb: float
    used_memory_gb: float
    free_memory_gb: float
    utilization_percent: float
    temperature_celsius: Optional[float] = None
    current_jobs: int = 0


@dataclass
class SystemResources:
    """Current system resource availability"""

    # CPU
    cpu_cores_total: int
    cpu_cores_available: int
    cpu_percent: float

    # Memory
    ram_total_gb: float
    ram_available_gb: float
    ram_percent: float

    # Disk
    disk_total_gb: float
    disk_available_gb: float
    disk_percent: float

    # GPU
    gpus: List[GPUStatus]


class ResourceManager:
    """
    Manage system resources for batch processing.

    Features:
    - GPU status monitoring
    - Memory tracking
    - CPU utilization
    - Disk space monitoring
    - Resource allocation
    - OOM detection and recovery

    Example:
        >>> manager = ResourceManager()
        >>> status = manager.get_system_resources()
        >>> if manager.can_allocate(requirements):
        ...     gpu_id = manager.allocate_gpu(requirements)
    """

    def __init__(self, reserve_memory_percent: float = 20.0):
        """
        Initialize resource manager.

        Args:
            reserve_memory_percent: Percentage of RAM to reserve for system
        """
        self.reserve_memory_percent = reserve_memory_percent

        # Track allocated resources
        self.allocated_gpus: Dict[int, int] = {}  # GPU ID -> job count
        self.allocated_cpu_cores: int = 0
        self.allocated_ram_gb: float = 0.0

        # GPU availability
        self.gpu_available = self._check_gpu_availability()

        if not self.gpu_available:
            logger.warning("No GPU detected or GPU libraries not available")

    # ========================================================================
    # GPU Detection and Monitoring
    # ========================================================================

    def _check_gpu_availability(self) -> bool:
        """Check if GPU and monitoring libraries are available"""
        try:
            import pynvml

            pynvml.nvmlInit()
            return True
        except:
            return False

    def get_gpu_count(self) -> int:
        """Get number of available GPUs"""
        if not self.gpu_available:
            return 0

        try:
            import pynvml

            return pynvml.nvmlDeviceGetCount()
        except:
            return 0

    def get_gpu_status(self, gpu_id: int) -> Optional[GPUStatus]:
        """
        Get status of specific GPU.

        Args:
            gpu_id: GPU index

        Returns:
            GPUStatus or None if not available
        """
        if not self.gpu_available:
            return None

        try:
            import pynvml

            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)

            # Get memory info
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            total_mem = mem_info.total / (1024**3)  # Convert to GB
            used_mem = mem_info.used / (1024**3)
            free_mem = mem_info.free / (1024**3)

            # Get name
            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode("utf-8")

            # Get utilization
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            utilization = util.gpu

            # Get temperature
            try:
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except:
                temp = None

            return GPUStatus(
                gpu_id=gpu_id,
                name=name,
                total_memory_gb=total_mem,
                used_memory_gb=used_mem,
                free_memory_gb=free_mem,
                utilization_percent=utilization,
                temperature_celsius=temp,
                current_jobs=self.allocated_gpus.get(gpu_id, 0),
            )

        except Exception as e:
            logger.error(f"Failed to get GPU {gpu_id} status: {e}")
            return None

    def get_all_gpu_status(self) -> List[GPUStatus]:
        """Get status of all GPUs"""
        gpu_count = self.get_gpu_count()
        statuses = []

        for i in range(gpu_count):
            status = self.get_gpu_status(i)
            if status:
                statuses.append(status)

        return statuses

    # ========================================================================
    # System Resource Monitoring
    # ========================================================================

    def get_system_resources(self) -> SystemResources:
        """
        Get current system resource availability.

        Returns:
            SystemResources snapshot
        """
        # CPU
        cpu_count = psutil.cpu_count(logical=True)
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_available = max(0, cpu_count - self.allocated_cpu_cores)

        # Memory
        mem = psutil.virtual_memory()
        ram_total = mem.total / (1024**3)
        ram_available = mem.available / (1024**3)

        # Reserve some memory for system
        reserve_gb = ram_total * (self.reserve_memory_percent / 100.0)
        ram_available = max(0, ram_available - reserve_gb - self.allocated_ram_gb)

        # Disk
        disk = psutil.disk_usage("/")
        disk_total = disk.total / (1024**3)
        disk_available = disk.free / (1024**3)

        # GPU
        gpus = self.get_all_gpu_status()

        return SystemResources(
            cpu_cores_total=cpu_count,
            cpu_cores_available=cpu_available,
            cpu_percent=cpu_percent,
            ram_total_gb=ram_total,
            ram_available_gb=ram_available,
            ram_percent=mem.percent,
            disk_total_gb=disk_total,
            disk_available_gb=disk_available,
            disk_percent=disk.percent,
            gpus=gpus,
        )

    # ========================================================================
    # Resource Allocation
    # ========================================================================

    def can_allocate(self, requirements: ResourceRequirements) -> bool:
        """
        Check if requirements can be allocated.

        Args:
            requirements: Resource requirements

        Returns:
            True if resources available
        """
        resources = self.get_system_resources()

        # Check GPU memory.
        #
        # When no GPU is present at all, the requirement is not satisfiable, so
        # refusing is correct: a job that genuinely needs 8 GB of VRAM cannot
        # run on CPU. What the scheduler must not do is sit in a silent retry
        # loop, which is why that refusal is reported through
        # explain_allocation_failure rather than returning a bare False.
        if requirements.gpu_memory_gb > 0:
            if not resources.gpus:
                return False
            gpu_ok = any(gpu.free_memory_gb >= requirements.gpu_memory_gb for gpu in resources.gpus)
            if not gpu_ok:
                return False

        # Check CPU cores
        if resources.cpu_cores_available < requirements.cpu_cores:
            return False

        # Check RAM
        if resources.ram_available_gb < requirements.ram_gb:
            return False

        # Check disk space
        if resources.disk_available_gb < requirements.disk_space_gb:
            return False

        return True

    def explain_allocation_failure(self, requirements: ResourceRequirements) -> Optional[str]:
        """
        Return why can_allocate would refuse, or None if it would succeed.

        can_allocate returning False is indistinguishable between "try again in
        a moment" and "this can never succeed on this host". A scheduler that
        only sees False cannot tell them apart, so it retries forever. This
        makes the permanent case nameable: no GPU present while the job wants
        VRAM, or a single request larger than total system RAM.
        """
        resources = self.get_system_resources()

        if requirements.gpu_memory_gb > 0 and not resources.gpus:
            return (
                f"job requires {requirements.gpu_memory_gb} GB of GPU memory but "
                "no GPU is visible to this process; the job cannot be scheduled "
                "here. Set generation_params={'prefer_gpu': False} to run it on "
                "CPU, or run on a host with a GPU."
            )

        if requirements.gpu_memory_gb > 0:
            best = max((gpu.free_memory_gb for gpu in resources.gpus), default=0.0)
            if best < requirements.gpu_memory_gb:
                return (
                    f"job requires {requirements.gpu_memory_gb} GB of GPU memory "
                    f"but the most free GPU has {round(best, 2)} GB"
                )

        if requirements.ram_gb > resources.ram_total_gb:
            return (
                f"job requires {requirements.ram_gb} GB RAM but the machine has "
                f"{round(resources.ram_total_gb, 2)} GB total"
            )

        if requirements.cpu_cores > resources.cpu_cores_total:
            return (
                f"job requires {requirements.cpu_cores} CPU cores but the machine "
                f"has {resources.cpu_cores_total}"
            )

        if requirements.disk_space_gb > resources.disk_available_gb:
            return (
                f"job requires {requirements.disk_space_gb} GB disk but only "
                f"{round(resources.disk_available_gb, 2)} GB is available"
            )

        return None

    def allocate_gpu(self, requirements: ResourceRequirements) -> Optional[int]:
        """
        Allocate GPU for job.

        Args:
            requirements: Resource requirements

        Returns:
            GPU ID or None if no GPU available
        """
        gpus = self.get_all_gpu_status()

        if not gpus:
            return None

        # Find GPU with most free memory that meets requirements
        best_gpu = None
        best_free_memory = 0.0

        for gpu in gpus:
            if gpu.free_memory_gb >= requirements.gpu_memory_gb:
                # Prefer GPU with no current jobs
                if gpu.current_jobs == 0:
                    best_gpu = gpu.gpu_id
                    break

                # Otherwise, find GPU with most free memory
                if gpu.free_memory_gb > best_free_memory:
                    best_free_memory = gpu.free_memory_gb
                    best_gpu = gpu.gpu_id

        if best_gpu is not None:
            # Track allocation
            self.allocated_gpus[best_gpu] = self.allocated_gpus.get(best_gpu, 0) + 1
            logger.info(f"Allocated GPU {best_gpu} (jobs: {self.allocated_gpus[best_gpu]})")

        return best_gpu

    def allocate_resources(self, requirements: ResourceRequirements) -> Dict[str, Any]:
        """
        Allocate all required resources.

        Args:
            requirements: Resource requirements

        Returns:
            Allocation info (gpu_id, cpu_cores, etc.)
        """
        if not self.can_allocate(requirements):
            return {}

        allocation = {}

        # Allocate GPU
        gpu_id = self.allocate_gpu(requirements)
        if gpu_id is not None:
            allocation["gpu_id"] = gpu_id

        # Allocate CPU cores
        self.allocated_cpu_cores += requirements.cpu_cores
        allocation["cpu_cores"] = requirements.cpu_cores

        # Allocate RAM
        self.allocated_ram_gb += requirements.ram_gb
        allocation["ram_gb"] = requirements.ram_gb

        logger.info(f"Allocated resources: {allocation}")
        return allocation

    def release_resources(self, allocation: Dict[str, Any]) -> None:
        """
        Release allocated resources.

        Args:
            allocation: Allocation info from allocate_resources()
        """
        # Release GPU
        if "gpu_id" in allocation:
            gpu_id = allocation["gpu_id"]
            if gpu_id in self.allocated_gpus:
                self.allocated_gpus[gpu_id] -= 1
                if self.allocated_gpus[gpu_id] <= 0:
                    del self.allocated_gpus[gpu_id]
                logger.info(f"Released GPU {gpu_id}")

        # Release CPU cores
        if "cpu_cores" in allocation:
            self.allocated_cpu_cores -= allocation["cpu_cores"]
            self.allocated_cpu_cores = max(0, self.allocated_cpu_cores)

        # Release RAM
        if "ram_gb" in allocation:
            self.allocated_ram_gb -= allocation["ram_gb"]
            self.allocated_ram_gb = max(0, self.allocated_ram_gb)

        logger.debug(f"Released resources: {allocation}")

    # ========================================================================
    # Resource Estimation
    # ========================================================================

    def estimate_requirements(
        self,
        prompt: str,
        output_type: str,
        target_engines: List[str],
        generation_params: Optional[Dict[str, Any]] = None,
    ) -> ResourceRequirements:
        """
        Estimate resource requirements for a job.

        GPU memory is derived from the actual GPUs present rather than assumed.
        A fixed 8 GB floor was wrong in both directions: on a host with a GPU
        smaller than 8 GB every job was permanently unschedulable, and on a host
        with no GPU at all the same constant made can_allocate refuse forever,
        so a batch sat at pending until an external timeout ended it.

        `prefer_gpu` selects the back end. When false, the requirement is CPU
        only and gpu_memory_gb is 0, which can_allocate already treats as "no
        GPU needed". Callers that know the work is CPU-viable should say so
        rather than relying on the absence of a GPU being tolerated.

        Args:
            prompt: Generation prompt
            output_type: Output type (character, environment, etc.)
            target_engines: Target engines
            generation_params: Generation parameters

        Returns:
            Estimated resource requirements
        """
        params = generation_params or {}

        width = params.get("width", 512)
        height = params.get("height", 512)
        steps = params.get("steps", 30)
        pixel_count = int(width) * int(height)

        # The diffusion base images at 512x512, so that is the reference size
        # and scales from there. No hard minimum: the size is a property of the
        # request, not a floor imposed on the host.
        reference_pixels = 512 * 512
        gpu_memory = round(8.0 * (pixel_count / reference_pixels), 2)
        gpu_memory = max(gpu_memory, 0.25)

        cpu_cores = 4
        ram = 16.0
        disk_space = 10.0
        duration = 60

        # More steps = more time
        if steps > 50:
            duration = 90
        elif steps > 100:
            duration = 120

        # Multiple engines = more disk space
        disk_space = 10.0 * len(target_engines)

        # Hero assets need more resources
        if params.get("is_hero_asset", False):
            gpu_memory *= 1.2
            ram *= 1.2
            duration = int(duration * 1.5)

        if not self._gpu_is_usable(params):
            # Either no GPU is present, or the caller explicitly asked for CPU.
            # Report no GPU requirement rather than an unsatisfiable one.
            gpu_memory = 0.0
            # CPU inference needs more host RAM than a small model on a GPU,
            # and a small slice of it is returned to the pool for a moment.
            ram = max(ram, 4.0)
            cpu_cores = max(cpu_cores, 2)

        return ResourceRequirements(
            gpu_memory_gb=round(gpu_memory, 2),
            cpu_cores=cpu_cores,
            ram_gb=ram,
            disk_space_gb=disk_space,
            max_duration_minutes=duration,
        )

    def _gpu_is_usable(self, params: Dict[str, Any]) -> bool:
        """
        Whether GPU memory should be requested for this job.

        False when the caller set prefer_gpu=False in generation_params, or when
        no GPU is visible to this process.
        """
        if params.get("prefer_gpu") is False:
            return False
        return bool(self.get_all_gpu_status())

    # ========================================================================
    # Monitoring and Health Checks
    # ========================================================================

    def check_system_health(self) -> Dict[str, Any]:
        """
        Check system health and resource availability.

        Returns:
            Health status dict
        """
        resources = self.get_system_resources()

        warnings = []
        errors = []

        # Check CPU
        if resources.cpu_percent > 90:
            warnings.append("CPU utilization high (>90%)")

        # Check RAM
        if resources.ram_percent > 90:
            warnings.append("RAM usage high (>90%)")
        if resources.ram_available_gb < 2.0:
            errors.append("Low RAM available (<2GB)")

        # Check disk
        if resources.disk_percent > 90:
            warnings.append("Disk usage high (>90%)")
        if resources.disk_available_gb < 10.0:
            errors.append("Low disk space (<10GB)")

        # Check GPUs
        for gpu in resources.gpus:
            if gpu.utilization_percent > 95:
                warnings.append(f"GPU {gpu.gpu_id} utilization high (>95%)")
            if gpu.free_memory_gb < 2.0:
                warnings.append(f"GPU {gpu.gpu_id} low memory (<2GB)")
            if gpu.temperature_celsius and gpu.temperature_celsius > 85:
                warnings.append(f"GPU {gpu.gpu_id} temperature high ({gpu.temperature_celsius}°C)")

        health_status = "healthy"
        if errors:
            health_status = "error"
        elif warnings:
            health_status = "warning"

        return {
            "status": health_status,
            "warnings": warnings,
            "errors": errors,
            "resources": resources,
        }

    def get_resource_summary(self) -> str:
        """Get human-readable resource summary"""
        resources = self.get_system_resources()

        lines = []
        lines.append("=== System Resources ===")

        # CPU
        lines.append(
            f"CPU: {resources.cpu_cores_available}/{resources.cpu_cores_total} cores available ({resources.cpu_percent:.1f}% used)"
        )

        # RAM
        lines.append(
            f"RAM: {resources.ram_available_gb:.1f}/{resources.ram_total_gb:.1f} GB available ({resources.ram_percent:.1f}% used)"
        )

        # Disk
        lines.append(
            f"Disk: {resources.disk_available_gb:.1f}/{resources.disk_total_gb:.1f} GB available ({resources.disk_percent:.1f}% used)"
        )

        # GPUs
        if resources.gpus:
            lines.append(f"\nGPUs: {len(resources.gpus)} detected")
            for gpu in resources.gpus:
                lines.append(f"  GPU {gpu.gpu_id} ({gpu.name}):")
                lines.append(
                    f"    Memory: {gpu.free_memory_gb:.1f}/{gpu.total_memory_gb:.1f} GB free"
                )
                lines.append(f"    Utilization: {gpu.utilization_percent:.0f}%")
                if gpu.temperature_celsius:
                    lines.append(f"    Temperature: {gpu.temperature_celsius}°C")
                lines.append(f"    Current jobs: {gpu.current_jobs}")
        else:
            lines.append("\nGPUs: None detected")

        return "\n".join(lines)
