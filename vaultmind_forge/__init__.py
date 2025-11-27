"""
VaultMind Forge - Complete Module Exports
138+ modules across Python, Rust, and C++
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("vaultmind-forge")
except PackageNotFoundError:
    __version__ = "0.1.0"

# Core modules - direct imports
__all__ = [
    # AI & Agents (23 modules)
    'forge_ai',
    'forge_agent',
    'forge_agents',

    # Generation (16 modules)
    'forge_diffusion',
    'forge_3d',
    'forge_video',
    'forge_procedural',

    # Processing (28 modules)
    'forge_intake',
    'forge_converter',
    'forge_batch',
    'forge_sr',
    'forge_semantic',

    # Validation (14 modules)
    'forge_validator',

    # Management (25 modules)
    'forge_executor',
    'forge_bots',
    'forge_monitor',
    'forge_packaging',
    'forge_lineage',
    'forge_versioning',

    # Interface (13 modules)
    'forge_cli',
    'cli',

    # Native (10 modules total)
    # - 7 Rust modules
    # - 3 C++ modules
]

# Quick access imports
def get_all_modules():
    """Returns list of all 138 available modules"""
    return {
        'python': 128,
        'rust': 7,
        'cpp': 3,
        'total': 138,
        'categories': {
            'ai_backends': 14,          # forge_ai
            'agents': 9,                # forge_agents
            'job_planning': 5,          # forge_agent
            'generation_image': 7,      # forge_diffusion
            'generation_video': 2,      # forge_video
            'generation_3d': 2,         # forge_3d
            'generation_procedural': 5, # forge_procedural
            'intake': 8,                # forge_intake
            'converter': 13,            # forge_converter
            'batch': 4,                 # forge_batch
            'sr_upscaling': 2,          # forge_sr
            'semantic': 2,              # forge_semantic
            'validation': 7,            # forge_validator
            'executor': 3,              # forge_executor
            'bots': 8,                  # forge_bots
            'monitor': 3,               # forge_monitor
            'packaging': 2,             # forge_packaging
            'lineage': 4,               # forge_lineage
            'versioning': 2,            # forge_versioning
            'cli_advanced': 12,         # cli
            'cli_basic': 1,             # forge_cli
            'native_cpp': 3,            # C++
            'native_rust': 7,           # Rust
            'tests': 13,                # Test suite
        }
    }

# Module status
MODULE_STATUS = {
    'production_ready': [
        'forge_intake', 'forge_converter', 'forge_monitor',
        'forge_semantic', 'forge_sr', 'forge_versioning',
        'forge_video', 'forge_agents', 'forge_bots',
        'forge_lineage', 'forge_packaging', 'forge_validator'
    ],
    'in_progress': [
        'forge_batch', 'forge_diffusion', 'forge_ai'
    ],
    'planned': [
        'forge_3d', 'forge_procedural'
    ]
}
