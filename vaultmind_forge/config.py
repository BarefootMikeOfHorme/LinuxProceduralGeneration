"""
VaultMind Forge - Configuration Loader
Loads JSON schemas, presets, and runtime config with environment variable overrides

L1-ACP Enhancement - Repair Priority #5
Integrates existing vaultmind_forge/config/ structure with Python runtime
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

# Project root detection
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "vaultmind_forge" / "config"
SCHEMAS_DIR = CONFIG_DIR / "schemas"
PRESETS_DIR = CONFIG_DIR / "presets"
RUNTIME_DIR = CONFIG_DIR / "runtime"


def load_json_config(path: Path) -> Dict[str, Any]:
    """Load JSON config file with error handling"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load config {path}: {e}")


def load_yaml_config(path: Path) -> Dict[str, Any]:
    """Load YAML config file with error handling"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        raise RuntimeError(f"Failed to load config {path}: {e}")


@dataclass
class PathConfig:
    """Path configuration with environment variable support"""

    # Core paths
    project_root: Path = PROJECT_ROOT
    config_dir: Path = CONFIG_DIR
    schemas_dir: Path = SCHEMAS_DIR
    presets_dir: Path = PRESETS_DIR
    runtime_dir: Path = RUNTIME_DIR

    # Virtual environment
    venv_path: Optional[Path] = None

    # Model and data paths
    models_dir: Path = PROJECT_ROOT / "models"
    output_dir: Path = PROJECT_ROOT / "output"
    checkpoints_dir: Path = PROJECT_ROOT / "checkpoints"

    # Script paths
    examples_dir: Path = PROJECT_ROOT / "examples"
    scripts_dir: Path = PROJECT_ROOT / "scripts"

    def __post_init__(self):
        """Auto-detect and load from environment"""
        # Auto-detect venv
        if venv_env := os.getenv("VAULTMIND_VENV_PATH"):
            self.venv_path = Path(venv_env)
        elif self.venv_path is None:
            for venv_name in [".venv312", ".venv", "venv"]:
                candidate = self.project_root / venv_name
                if candidate.exists():
                    self.venv_path = candidate
                    break

        # Environment overrides
        if models := os.getenv("VAULTMIND_MODELS_DIR"):
            self.models_dir = Path(models)
        if output := os.getenv("VAULTMIND_OUTPUT_DIR"):
            self.output_dir = Path(output)
        if checkpoints := os.getenv("VAULTMIND_CHECKPOINTS_DIR"):
            self.checkpoints_dir = Path(checkpoints)


@dataclass
class RuntimeConfig:
    """Runtime defaults - can be overridden by environment variables"""

    # Generation defaults (from AUDIT_REPORT magic numbers)
    default_width: int = 1024
    default_height: int = 1024
    default_steps: int = 30
    default_batch_size: int = 1

    # Timeouts (seconds)
    generation_timeout: int = 300
    validation_timeout: int = 60
    default_task_timeout: int = 300

    # Workflow settings
    max_parallel_tasks: int = 4
    checkpoint_interval: float = 30.0
    dag_poll_interval: float = 0.1

    # Monitor refresh
    monitor_refresh_interval: int = 2

    # Agent autonomy levels (from AUDIT_REPORT)
    agent_quality_guardian_autonomy: float = 0.75
    agent_prompt_refiner_autonomy: float = 0.85
    agent_parameter_optimizer_autonomy: float = 0.70
    agent_material_specialist_autonomy: float = 0.75
    agent_resolution_expert_autonomy: float = 0.80

    def __post_init__(self):
        """Load from environment variables"""
        if w := os.getenv("VAULTMIND_DEFAULT_WIDTH"):
            self.default_width = int(w)
        if h := os.getenv("VAULTMIND_DEFAULT_HEIGHT"):
            self.default_height = int(h)
        if s := os.getenv("VAULTMIND_DEFAULT_STEPS"):
            self.default_steps = int(s)
        if t := os.getenv("VAULTMIND_GENERATION_TIMEOUT"):
            self.generation_timeout = int(t)
        if m := os.getenv("VAULTMIND_MAX_PARALLEL_TASKS"):
            self.max_parallel_tasks = int(m)


@dataclass
class AIControlConfig:
    """AI control configuration from JSON schemas/presets"""

    pipeline_stage: str = "generation"
    ai_authority_level: str = "high_autonomy"
    confidence_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "auto_approve": 0.85,
        "auto_fix": 0.75,
        "flag_for_review": 0.60,
        "auto_reject": 0.40
    })
    decision_points: list = field(default_factory=list)
    human_override: Dict[str, Any] = field(default_factory=dict)
    learning_feedback: Dict[str, Any] = field(default_factory=dict)
    fallback_strategies: list = field(default_factory=list)
    monitoring: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_preset(cls, preset_name: str) -> AIControlConfig:
        """Load from preset JSON file"""
        preset_path = PRESETS_DIR / f"{preset_name}.json"
        if not preset_path.exists():
            raise FileNotFoundError(f"Preset {preset_name} not found at {preset_path}")

        data = load_json_config(preset_path)
        return cls(**data)


@dataclass
class VaultMindConfig:
    """
    Complete VaultMind Forge configuration

    Loads from:
    - vaultmind_forge/config/schemas/ (JSON schemas)
    - vaultmind_forge/config/presets/ (JSON presets)
    - config/model_paths.yaml (model locations)
    - Environment variables (overrides)
    """

    paths: PathConfig = field(default_factory=PathConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    ai_control: Optional[AIControlConfig] = None

    # Model paths from YAML
    model_paths: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Load additional configs"""
        # Load model paths YAML
        model_config = PROJECT_ROOT / "config" / "model_paths.yaml"
        if model_config.exists():
            self.model_paths = load_yaml_config(model_config)

        # Load default AI control preset if specified
        if ai_preset := os.getenv("VAULTMIND_AI_PRESET"):
            try:
                self.ai_control = AIControlConfig.from_preset(ai_preset)
            except Exception as e:
                print(f"Warning: Could not load AI preset '{ai_preset}': {e}")

    def get_model_path(self, model_name: str) -> Optional[Path]:
        """Get path for specific model"""
        if model_name in self.model_paths:
            return Path(self.model_paths[model_name]['path'])
        return None

    def load_ai_preset(self, preset_name: str):
        """Load AI control preset"""
        self.ai_control = AIControlConfig.from_preset(preset_name)

    def get_preset_names(self) -> list[str]:
        """List available preset names"""
        return [p.stem for p in PRESETS_DIR.glob("*.json")]


# Singleton instance
_config: Optional[VaultMindConfig] = None


def get_config() -> VaultMindConfig:
    """
    Get global configuration (singleton)

    Example:
        >>> from vaultmind_forge.config import get_config
        >>> config = get_config()
        >>> print(config.paths.venv_path)
        >>> print(config.runtime.default_width)
        >>> config.load_ai_preset("ai_full_autonomy")
    """
    global _config
    if _config is None:
        _config = VaultMindConfig()
    return _config


def reload_config() -> VaultMindConfig:
    """Force reload configuration"""
    global _config
    _config = VaultMindConfig()
    return _config


__all__ = [
    "VaultMindConfig",
    "PathConfig",
    "RuntimeConfig",
    "AIControlConfig",
    "get_config",
    "reload_config",
    "PROJECT_ROOT",
    "CONFIG_DIR",
]
