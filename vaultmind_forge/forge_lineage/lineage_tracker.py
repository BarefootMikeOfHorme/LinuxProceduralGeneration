"""
VaultMind Forge - Lineage Tracker
Complete asset genealogy tracking with SHA-256 checksums and parent relationships
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class OperationType(Enum):
    """Types of operations tracked in lineage"""
    GENERATION = "generation"
    VALIDATION = "validation"
    CONVERSION = "conversion"
    OPTIMIZATION = "optimization"
    EXPORT = "export"
    RETRY = "retry"


@dataclass
class LineageRecord:
    """Single lineage record for an asset"""
    sha256: str
    timestamp: str
    operation: str
    generator: str
    parent: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    validation_scores: Optional[Dict[str, float]] = None
    ai_decision: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}


class LineageTracker:
    """
    Track complete asset genealogy throughout the pipeline.

    Features:
    - SHA-256 checksum for every asset
    - Parent-child relationships
    - Operation history (generation, validation, conversion)
    - Parameter tracking
    - Quality scores
    - AI decisions
    - Full genealogy reconstruction

    Example:
        >>> tracker = LineageTracker()
        >>>
        >>> # Record generation
        >>> gen_checksum = tracker.record_generation(
        ...     asset_path="output/char_001.png",
        ...     parameters={"prompt": "knight", "steps": 30}
        ... )
        >>>
        >>> # Record validation
        >>> tracker.record_validation(
        ...     asset_path="output/char_001.png",
        ...     scores={"sharpness": 0.85, "overall": 0.82}
        ... )
        >>>
        >>> # Record conversion
        >>> tracker.record_conversion(
        ...     input_asset="output/char_001.png",
        ...     output_asset="output/char_001.dds",
        ...     format="dds"
        ... )
        >>>
        >>> # Get full history
        >>> history = tracker.get_asset_history(gen_checksum)
    """

    def __init__(
        self,
        base_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize lineage tracker

        Args:
            base_path: Base directory for lineage storage (default: assets/lineage)
            logger: Optional logger
        """
        if base_path is None:
            # Default to assets/lineage
            base_path = Path(__file__).parents[2] / "assets" / "lineage"

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.logger = logger or self._setup_logger()

        # In-memory cache for fast lookups
        self._cache: Dict[str, LineageRecord] = {}

    def _setup_logger(self) -> logging.Logger:
        """Set up default logger"""
        logger = logging.getLogger("VaultMindForge.Lineage")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)
        return logger

    def compute_checksum(self, file_path: Path) -> str:
        """
        Compute SHA-256 checksum for a file

        Args:
            file_path: Path to file

        Returns:
            SHA-256 hex digest
        """
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def record_generation(
        self,
        asset_path: Path | str,
        parameters: Dict[str, Any],
        generator: str = "forge_diffusion",
        parent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record generation of a new asset

        Args:
            asset_path: Path to generated asset
            parameters: Generation parameters (prompt, steps, cfg, etc.)
            generator: Generator module name
            parent: Optional parent asset checksum (for img2img, variations)
            metadata: Additional metadata

        Returns:
            SHA-256 checksum of asset
        """
        asset_path = Path(asset_path)

        if not asset_path.exists():
            raise FileNotFoundError(f"Asset not found: {asset_path}")

        # Compute checksum
        checksum = self.compute_checksum(asset_path)

        # Create lineage record
        record = LineageRecord(
            sha256=checksum,
            timestamp=datetime.now().isoformat(),
            operation=OperationType.GENERATION.value,
            generator=generator,
            parent=parent,
            parameters=parameters,
            metadata=metadata
        )

        # Save record
        self._save_lineage(checksum, record)

        self.logger.info(f"Recorded generation: {checksum[:16]}... ({asset_path.name})")

        return checksum

    def record_validation(
        self,
        asset_path: Path | str,
        scores: Dict[str, float],
        ai_decision: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record validation results for an asset

        Args:
            asset_path: Path to asset
            scores: Validation scores (sharpness, anatomy, etc.)
            ai_decision: AI decision info (decision, confidence, reasoning)

        Returns:
            SHA-256 checksum of asset
        """
        asset_path = Path(asset_path)

        if not asset_path.exists():
            raise FileNotFoundError(f"Asset not found: {asset_path}")

        checksum = self.compute_checksum(asset_path)

        # Check if record exists
        existing = self._load_lineage(checksum)

        if existing:
            # Update existing record with validation info
            existing.validation_scores = scores
            existing.ai_decision = ai_decision
            self._save_lineage(checksum, existing)
        else:
            # Create new record (validation-only)
            record = LineageRecord(
                sha256=checksum,
                timestamp=datetime.now().isoformat(),
                operation=OperationType.VALIDATION.value,
                generator="forge_validator",
                validation_scores=scores,
                ai_decision=ai_decision
            )
            self._save_lineage(checksum, record)

        self.logger.info(f"Recorded validation: {checksum[:16]}... (score: {scores.get('overall', 0.0):.2f})")

        return checksum

    def record_conversion(
        self,
        input_asset: Path | str,
        output_asset: Path | str,
        format: str,
        converter: str = "forge_converter",
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record format conversion

        Args:
            input_asset: Input asset path
            output_asset: Output asset path
            format: Target format
            converter: Converter module name
            parameters: Conversion parameters

        Returns:
            SHA-256 checksum of output asset
        """
        input_path = Path(input_asset)
        output_path = Path(output_asset)

        if not input_path.exists():
            raise FileNotFoundError(f"Input asset not found: {input_path}")
        if not output_path.exists():
            raise FileNotFoundError(f"Output asset not found: {output_path}")

        # Compute checksums
        input_checksum = self.compute_checksum(input_path)
        output_checksum = self.compute_checksum(output_path)

        # Create lineage record for output
        record = LineageRecord(
            sha256=output_checksum,
            timestamp=datetime.now().isoformat(),
            operation=OperationType.CONVERSION.value,
            generator=converter,
            parent=input_checksum,
            parameters={"format": format, **(parameters or {})},
            metadata={
                "input_file": str(input_path),
                "output_file": str(output_path)
            }
        )

        # Save record
        self._save_lineage(output_checksum, record)

        self.logger.info(f"Recorded conversion: {input_checksum[:16]}... -> {output_checksum[:16]}... ({format})")

        return output_checksum

    def record_optimization(
        self,
        input_asset: Path | str,
        output_asset: Path | str,
        optimization_type: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Record asset optimization (LOD, compression, etc.)

        Args:
            input_asset: Input asset path
            output_asset: Output asset path
            optimization_type: Type of optimization
            parameters: Optimization parameters

        Returns:
            SHA-256 checksum of output asset
        """
        input_path = Path(input_asset)
        output_path = Path(output_asset)

        if not input_path.exists():
            raise FileNotFoundError(f"Input asset not found: {input_path}")
        if not output_path.exists():
            raise FileNotFoundError(f"Output asset not found: {output_path}")

        input_checksum = self.compute_checksum(input_path)
        output_checksum = self.compute_checksum(output_path)

        record = LineageRecord(
            sha256=output_checksum,
            timestamp=datetime.now().isoformat(),
            operation=OperationType.OPTIMIZATION.value,
            generator="forge_converter",
            parent=input_checksum,
            parameters={"optimization_type": optimization_type, **parameters}
        )

        self._save_lineage(output_checksum, record)

        self.logger.info(f"Recorded optimization: {optimization_type} {output_checksum[:16]}...")

        return output_checksum

    def record_retry(
        self,
        original_asset: Path | str,
        retry_asset: Path | str,
        attempt_number: int,
        adjustments: Dict[str, Any]
    ) -> str:
        """
        Record retry attempt

        Args:
            original_asset: Original (failed) asset path
            retry_asset: Retry asset path
            attempt_number: Retry attempt number
            adjustments: Parameter adjustments applied

        Returns:
            SHA-256 checksum of retry asset
        """
        original_path = Path(original_asset)
        retry_path = Path(retry_asset)

        if not original_path.exists():
            raise FileNotFoundError(f"Original asset not found: {original_path}")
        if not retry_path.exists():
            raise FileNotFoundError(f"Retry asset not found: {retry_path}")

        original_checksum = self.compute_checksum(original_path)
        retry_checksum = self.compute_checksum(retry_path)

        record = LineageRecord(
            sha256=retry_checksum,
            timestamp=datetime.now().isoformat(),
            operation=OperationType.RETRY.value,
            generator="forge_diffusion",
            parent=original_checksum,
            parameters={
                "attempt_number": attempt_number,
                "adjustments": adjustments
            }
        )

        self._save_lineage(retry_checksum, record)

        self.logger.info(f"Recorded retry: attempt {attempt_number}, {retry_checksum[:16]}...")

        return retry_checksum

    def get_asset_history(self, checksum: str) -> List[LineageRecord]:
        """
        Get complete history of an asset (full genealogy)

        Args:
            checksum: Asset SHA-256 checksum

        Returns:
            List of LineageRecord objects (from oldest ancestor to current)
        """
        history = []
        current_checksum = checksum

        # Traverse parent chain
        visited = set()
        while current_checksum:
            if current_checksum in visited:
                # Circular reference detected
                self.logger.warning(f"Circular reference in lineage: {current_checksum}")
                break

            visited.add(current_checksum)

            record = self._load_lineage(current_checksum)
            if not record:
                break

            history.append(record)
            current_checksum = record.parent

        # Reverse to get chronological order (oldest first)
        history.reverse()

        return history

    def get_children(self, checksum: str) -> List[LineageRecord]:
        """
        Get all children (derivatives) of an asset

        Args:
            checksum: Parent asset SHA-256 checksum

        Returns:
            List of child LineageRecord objects
        """
        children = []

        # Search all lineage files for this parent
        for lineage_file in self.base_path.glob("*.json"):
            record = self._load_lineage_from_file(lineage_file)
            if record and record.parent == checksum:
                children.append(record)

        return children

    def get_asset_tree(self, checksum: str, max_depth: int = 10) -> Dict[str, Any]:
        """
        Get complete asset tree (ancestors and descendants)

        Args:
            checksum: Asset SHA-256 checksum
            max_depth: Maximum tree depth

        Returns:
            Tree structure as nested dict
        """
        record = self._load_lineage(checksum)
        if not record:
            return {}

        tree = {
            "checksum": checksum,
            "operation": record.operation,
            "generator": record.generator,
            "timestamp": record.timestamp,
            "children": []
        }

        if max_depth > 0:
            children = self.get_children(checksum)
            for child in children:
                child_tree = self.get_asset_tree(child.sha256, max_depth - 1)
                tree["children"].append(child_tree)

        return tree

    def _save_lineage(self, checksum: str, record: LineageRecord):
        """Save lineage record to disk"""
        # Update cache
        self._cache[checksum] = record

        # Save to file
        lineage_file = self.base_path / f"{checksum}.json"
        with open(lineage_file, 'w', encoding='utf-8') as f:
            json.dump(record.to_dict(), f, indent=2)

    def _load_lineage(self, checksum: str) -> Optional[LineageRecord]:
        """Load lineage record from disk or cache"""
        # Check cache first
        if checksum in self._cache:
            return self._cache[checksum]

        # Load from file
        lineage_file = self.base_path / f"{checksum}.json"
        return self._load_lineage_from_file(lineage_file)

    def _load_lineage_from_file(self, lineage_file: Path) -> Optional[LineageRecord]:
        """Load lineage record from file"""
        if not lineage_file.exists():
            return None

        try:
            with open(lineage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            record = LineageRecord(
                sha256=data["sha256"],
                timestamp=data["timestamp"],
                operation=data["operation"],
                generator=data["generator"],
                parent=data.get("parent"),
                parameters=data.get("parameters"),
                validation_scores=data.get("validation_scores"),
                ai_decision=data.get("ai_decision"),
                metadata=data.get("metadata")
            )

            # Update cache
            self._cache[record.sha256] = record

            return record
        except Exception as e:
            self.logger.error(f"Failed to load lineage from {lineage_file}: {e}")
            return None

    def export_genealogy(self, checksum: str, output_path: Path):
        """
        Export complete genealogy as JSON

        Args:
            checksum: Asset checksum
            output_path: Output JSON file path
        """
        tree = self.get_asset_tree(checksum)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tree, f, indent=2)

        self.logger.info(f"Exported genealogy to {output_path}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get lineage statistics"""
        total_assets = len(list(self.base_path.glob("*.json")))

        operations = {}
        for lineage_file in self.base_path.glob("*.json"):
            record = self._load_lineage_from_file(lineage_file)
            if record:
                operations[record.operation] = operations.get(record.operation, 0) + 1

        return {
            "total_assets": total_assets,
            "operations": operations,
            "storage_path": str(self.base_path)
        }
