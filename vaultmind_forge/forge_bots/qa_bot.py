"""
VaultMind Forge - Quality Assurance Bot
Continuous asset quality validation
"""

from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import logging

# Add parent to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from .base_bot import BaseBot, BotConfig, BotPriority

logger = logging.getLogger(__name__)


@dataclass
class QAConfig:
    """QA bot configuration"""
    asset_library_path: Path
    validation_patterns: List[str] = field(default_factory=lambda: ["**/*.fbx", "**/*.png", "**/*.dds"])
    min_quality_threshold: float = 0.7
    report_path: Optional[Path] = None
    auto_repair: bool = False


@dataclass
class QAReport:
    """QA scan report"""
    timestamp: datetime
    total_assets: int
    passed: int
    failed: int
    warnings: int
    issues: List[Dict]

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_assets': self.total_assets,
            'passed': self.passed,
            'failed': self.failed,
            'warnings': self.warnings,
            'success_rate': (self.passed / self.total_assets * 100) if self.total_assets > 0 else 0,
            'issues': self.issues
        }


class QualityAssuranceBot(BaseBot):
    """
    Quality assurance bot - validates asset library quality.

    Features:
    - Continuous library scanning
    - Quality metrics tracking
    - Issue detection and reporting
    - Optional auto-repair
    - Historical quality trends

    Example:
        config = BotConfig(
            name="qa_bot",
            check_interval_seconds=3600.0  # Every hour
        )

        qa_config = QAConfig(
            asset_library_path=Path("output/assets"),
            min_quality_threshold=0.7,
            auto_repair=False
        )

        bot = QualityAssuranceBot(config, qa_config)
        bot.start()
    """

    def __init__(self, config: BotConfig, qa_config: QAConfig):
        super().__init__(config)

        self.qa_config = qa_config
        self.reports: List[QAReport] = []
        self.max_reports = 100

        # Stats
        self.total_scans = 0
        self.total_issues_found = 0
        self.total_repairs = 0

        logger.info(f"QA bot initialized for {qa_config.asset_library_path}")

    def execute_action(self) -> bool:
        """
        Execute QA scan - validate asset library.

        Returns:
            True if scan completed
        """
        if not self.qa_config.asset_library_path.exists():
            logger.warning(f"Asset library not found: {self.qa_config.asset_library_path}")
            return False

        # Scan library
        report = self._scan_library()

        # Store report
        self.reports.append(report)
        if len(self.reports) > self.max_reports:
            self.reports = self.reports[-self.max_reports:]

        # Save report if configured
        if self.qa_config.report_path:
            self._save_report(report)

        # Create alerts for critical issues
        if report.failed > 0:
            self.create_alert(
                'quality_issues',
                f"Found {report.failed} failed assets in scan",
                severity='high' if report.failed > 10 else 'medium'
            )

        self.total_scans += 1
        return True

    def _scan_library(self) -> QAReport:
        """
        Scan asset library and generate report.

        Returns:
            QA report
        """
        total_assets = 0
        passed = 0
        failed = 0
        warnings = 0
        issues = []

        # Scan each pattern
        for pattern in self.qa_config.validation_patterns:
            files = list(self.qa_config.asset_library_path.glob(pattern))

            for file_path in files:
                if not file_path.is_file():
                    continue

                total_assets += 1

                # Validate asset (placeholder - would use forge_validator)
                try:
                    is_valid, issue = self._validate_asset(file_path)

                    if is_valid:
                        passed += 1
                    else:
                        failed += 1
                        issues.append(issue)
                        self.total_issues_found += 1

                        # Auto-repair if enabled
                        if self.qa_config.auto_repair:
                            if self._attempt_repair(file_path, issue):
                                self.total_repairs += 1

                except Exception as e:
                    logger.error(f"Error validating {file_path}: {e}")
                    warnings += 1
                    issues.append({
                        'file': str(file_path),
                        'severity': 'warning',
                        'issue': f"Validation error: {e}"
                    })

        return QAReport(
            timestamp=datetime.now(),
            total_assets=total_assets,
            passed=passed,
            failed=failed,
            warnings=warnings,
            issues=issues
        )

    def _validate_asset(self, file_path: Path) -> tuple[bool, Optional[Dict]]:
        """
        Validate single asset.

        Args:
            file_path: Asset path

        Returns:
            (is_valid, issue_dict)
        """
        # Placeholder validation - in real implementation would use forge_validator
        # For now, just check file size and existence
        try:
            size_mb = file_path.stat().st_size / (1024 ** 2)

            # Simple checks
            if size_mb == 0:
                return False, {
                    'file': str(file_path),
                    'severity': 'critical',
                    'issue': 'Empty file'
                }

            if size_mb > 500:  # Over 500MB
                return False, {
                    'file': str(file_path),
                    'severity': 'warning',
                    'issue': f'Large file size: {size_mb:.1f} MB'
                }

            return True, None

        except Exception as e:
            return False, {
                'file': str(file_path),
                'severity': 'error',
                'issue': str(e)
            }

    def _attempt_repair(self, file_path: Path, issue: Dict) -> bool:
        """
        Attempt to repair asset issue.

        Args:
            file_path: Asset path
            issue: Issue description

        Returns:
            True if repaired
        """
        # Placeholder - would implement actual repair logic
        logger.info(f"Attempting repair for {file_path}: {issue['issue']}")
        return False

    def _save_report(self, report: QAReport) -> None:
        """Save report to file"""
        import json

        report_file = self.qa_config.report_path / f"qa_report_{report.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)

        logger.info(f"QA report saved: {report_file}")

    def get_qa_status(self) -> Dict:
        """Get QA status"""
        latest_report = self.reports[-1] if self.reports else None

        return {
            'total_scans': self.total_scans,
            'total_issues_found': self.total_issues_found,
            'total_repairs': self.total_repairs,
            'latest_scan': latest_report.to_dict() if latest_report else None,
        }

    def print_status(self) -> None:
        """Print formatted status"""
        super().print_status()

        qa_status = self.get_qa_status()

        print(f"QA STATUS:")
        print(f"  Total Scans: {qa_status['total_scans']}")
        print(f"  Issues Found: {qa_status['total_issues_found']}")
        print(f"  Repairs: {qa_status['total_repairs']}")

        if qa_status['latest_scan']:
            scan = qa_status['latest_scan']
            print(f"\nLATEST SCAN:")
            print(f"  Assets: {scan['total_assets']}")
            print(f"  Passed: {scan['passed']} ({scan['success_rate']:.1f}%)")
            print(f"  Failed: {scan['failed']}")
            print(f"  Warnings: {scan['warnings']}")

        print()
