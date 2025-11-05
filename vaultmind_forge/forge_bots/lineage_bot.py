"""
VaultMind Forge - Lineage Inspector Bot
Monitors asset lineage integrity
"""

from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Set
from datetime import datetime
import logging

# Add parent to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from .base_bot import BaseBot, BotConfig

logger = logging.getLogger(__name__)


@dataclass
class LineageConfig:
    """Lineage inspector configuration"""
    lineage_db_path: Path
    asset_library_path: Path
    check_orphans: bool = True
    check_broken_chains: bool = True
    check_missing_files: bool = True


class LineageInspectorBot(BaseBot):
    """
    Lineage inspector bot - monitors asset genealogy integrity.

    Features:
    - Orphan detection (assets without parents)
    - Broken chain detection (missing parent references)
    - Missing file detection (lineage exists but file doesn't)
    - Integrity reporting

    Example:
        config = BotConfig(
            name="lineage_inspector",
            check_interval_seconds=1800.0  # Every 30 minutes
        )

        lineage_config = LineageConfig(
            lineage_db_path=Path("lineage"),
            asset_library_path=Path("output/assets")
        )

        bot = LineageInspectorBot(config, lineage_config)
        bot.start()
    """

    def __init__(self, config: BotConfig, lineage_config: LineageConfig):
        super().__init__(config)

        self.lineage_config = lineage_config

        # Stats
        self.total_checks = 0
        self.orphans_found = 0
        self.broken_chains_found = 0
        self.missing_files_found = 0

        logger.info("Lineage inspector initialized")

    def execute_action(self) -> bool:
        """
        Execute lineage check.

        Returns:
            True if check completed
        """
        if not self.lineage_config.lineage_db_path.exists():
            logger.warning(f"Lineage DB not found: {self.lineage_config.lineage_db_path}")
            return False

        issues_found = 0

        # Check for orphans
        if self.lineage_config.check_orphans:
            orphans = self._check_orphans()
            if orphans:
                issues_found += len(orphans)
                self.orphans_found += len(orphans)
                self.create_alert(
                    'orphans_detected',
                    f"Found {len(orphans)} orphaned assets",
                    severity='medium'
                )

        # Check for broken chains
        if self.lineage_config.check_broken_chains:
            broken = self._check_broken_chains()
            if broken:
                issues_found += len(broken)
                self.broken_chains_found += len(broken)
                self.create_alert(
                    'broken_chains_detected',
                    f"Found {len(broken)} broken lineage chains",
                    severity='high'
                )

        # Check for missing files
        if self.lineage_config.check_missing_files:
            missing = self._check_missing_files()
            if missing:
                issues_found += len(missing)
                self.missing_files_found += len(missing)
                self.create_alert(
                    'missing_files_detected',
                    f"Found {len(missing)} missing asset files",
                    severity='high'
                )

        self.total_checks += 1
        return True

    def _check_orphans(self) -> List[str]:
        """
        Check for orphaned assets (no parent reference).

        Returns:
            List of orphaned asset checksums
        """
        # Placeholder - would integrate with forge_lineage
        orphans = []

        # Scan lineage files
        lineage_files = list(self.lineage_config.lineage_db_path.glob("*.json"))

        for lineage_file in lineage_files:
            try:
                import json
                with open(lineage_file, 'r') as f:
                    data = json.load(f)

                # Check if has parent
                if not data.get('parent'):
                    # Check if it's a root asset (should have generator)
                    if data.get('operation') != 'GENERATION':
                        orphans.append(data.get('sha256', str(lineage_file)))

            except Exception as e:
                logger.error(f"Error checking lineage file {lineage_file}: {e}")

        return orphans

    def _check_broken_chains(self) -> List[Dict]:
        """
        Check for broken lineage chains (parent doesn't exist).

        Returns:
            List of broken chains
        """
        broken = []

        lineage_files = list(self.lineage_config.lineage_db_path.glob("*.json"))
        checksums: Set[str] = set()

        # Build set of known checksums
        for lineage_file in lineage_files:
            try:
                import json
                with open(lineage_file, 'r') as f:
                    data = json.load(f)
                    checksums.add(data.get('sha256', ''))
            except:
                pass

        # Check for broken references
        for lineage_file in lineage_files:
            try:
                import json
                with open(lineage_file, 'r') as f:
                    data = json.load(f)

                parent = data.get('parent')
                if parent and parent not in checksums:
                    broken.append({
                        'asset': data.get('sha256'),
                        'missing_parent': parent
                    })

            except Exception as e:
                logger.error(f"Error checking chain {lineage_file}: {e}")

        return broken

    def _check_missing_files(self) -> List[str]:
        """
        Check for assets with lineage but missing files.

        Returns:
            List of missing assets
        """
        missing = []

        lineage_files = list(self.lineage_config.lineage_db_path.glob("*.json"))

        for lineage_file in lineage_files:
            try:
                import json
                with open(lineage_file, 'r') as f:
                    data = json.load(f)

                # Check if asset file exists (would need metadata about file path)
                # Placeholder for now
                pass

            except Exception as e:
                logger.error(f"Error checking file {lineage_file}: {e}")

        return missing

    def get_lineage_status(self) -> Dict:
        """Get lineage status"""
        return {
            'total_checks': self.total_checks,
            'orphans_found': self.orphans_found,
            'broken_chains_found': self.broken_chains_found,
            'missing_files_found': self.missing_files_found,
        }

    def print_status(self) -> None:
        """Print formatted status"""
        super().print_status()

        lineage_status = self.get_lineage_status()

        print(f"LINEAGE STATUS:")
        print(f"  Total Checks: {lineage_status['total_checks']}")
        print(f"  Orphans Found: {lineage_status['orphans_found']}")
        print(f"  Broken Chains: {lineage_status['broken_chains_found']}")
        print(f"  Missing Files: {lineage_status['missing_files_found']}")
        print()
