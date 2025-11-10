"""
VaultMind Forge - Asset Intake System
=====================================

Comprehensive asset intake, classification, and progressive enhancement pipeline.

Pipeline Stages:
  1. INTAKE: Scan and catalog raw downloads (archives, models, textures)
  2. EXTRACTION: Unpack archives, organize by type
  3. CLASSIFICATION: AI-assisted categorization with deep metadata
  4. VALIDATION: Quality checks, format verification
  5. ENHANCEMENT: Progressive quality improvements (low → med → high fidelity)
  6. CONVERSION: Multi-engine format preparation
  7. CATALOGING: Final registry with searchable metadata

Philosophy:
- **AI-Explained Metadata**: Every schema field has AI-readable explanations
- **Progressive Enhancement**: Assets improve through pipeline stages
- **Semantic Tagging**: Deep, hierarchical tag system for discoverability
- **Quality Tracking**: Each stage tracks quality metrics and improvements
- **Lineage Preservation**: Complete provenance from download to final asset
"""

from enum import Enum
from typing import List

__version__ = "1.0.0"
__author__ = "VaultMind Forge"


class IntakeStage(Enum):
    """Asset intake pipeline stages"""
    RAW = "raw"                          # Downloaded, unprocessed
    EXTRACTED = "extracted"              # Unpacked from archives
    CLASSIFIED = "classified"            # Categorized with metadata
    VALIDATED = "validated"              # Quality-checked
    ENHANCED = "enhanced"                # Quality-improved
    CONVERTED = "converted"              # Engine-ready formats
    CATALOGED = "cataloged"              # Final registry entry


class QualityLevel(Enum):
    """Asset quality/fidelity levels"""
    UNKNOWN = "unknown"
    LOW = "low"                          # Preview, low-poly
    MEDIUM = "medium"                    # Game-ready
    HIGH = "high"                        # High-fidelity
    ULTRA = "ultra"                      # Production, cinematic


class AssetCategory(Enum):
    """Primary asset categories"""
    CHARACTERS = "characters"
    VEHICLES = "vehicles"
    WEAPONS = "weapons"
    BUILDINGS = "buildings"
    NATURE = "nature"
    PROPS = "props"
    ENVIRONMENTS = "environments"
    EFFECTS = "effects"
    ANIMALS = "animals"
    ARCHITECTURE = "architecture"
    FURNITURE = "furniture"
    UNCATEGORIZED = "uncategorized"


def get_supported_stages() -> List[str]:
    """Get list of pipeline stages"""
    return [stage.value for stage in IntakeStage]


def get_supported_quality_levels() -> List[str]:
    """Get list of quality levels"""
    return [level.value for level in QualityLevel]


def get_supported_categories() -> List[str]:
    """Get list of asset categories"""
    return [cat.value for cat in AssetCategory]


__all__ = [
    'IntakeStage',
    'QualityLevel',
    'AssetCategory',
    'get_supported_stages',
    'get_supported_quality_levels',
    'get_supported_categories',
]
