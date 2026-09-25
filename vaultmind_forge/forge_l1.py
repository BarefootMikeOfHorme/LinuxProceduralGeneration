"""Safe Python interface to the AL1/LPG-L1 scanner.

This module is intentionally read-only. Mutating scanner operations remain
behind the scanner's own explicit confirmation and safety flows.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Sequence


class AL1ScannerError(RuntimeError):
    """Raised when the AL1 scanner cannot be safely invoked."""


def default_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _scanner_command(root: Path) -> list[str]:
    configured = os.environ.get("LPG_AL1SCAN_BIN")
    if configured:
        candidate = Path(configured).expanduser()
        if not candidate.is_file():
            raise AL1ScannerError(f"LPG_AL1SCAN_BIN does not exist: {candidate}")
        return [str(candidate)]

    names = ["al1scan.exe"] if os.name == "nt" else ["al1scan"]
    for name in names:
        candidate = root / "al1scan" / "target" / "release" / name
        if candidate.is_file():
            return [str(candidate)]

    raise AL1ScannerError(
        "AL1 scanner binary is not installed. Set LPG_AL1SCAN_BIN or build "
        "al1scan/target/release before using forge AL1 commands."
    )


def build_scanner_args(
    root: Path,
    operation_args: Sequence[str],
    scope: str | None = None,
) -> list[str]:
    command = _scanner_command(root)
    if scope:
        command.extend(["--scope", scope])
    command.extend(operation_args)
    command.append(str(root))
    return command


def run_scanner(
    root: Path | None = None,
    operation_args: Sequence[str] = (),
    scope: str | None = None,
    timeout_seconds: int = 60,
) -> Any:
    project_root = (root or default_project_root()).resolve()
    command = build_scanner_args(project_root, operation_args, scope)
    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise AL1ScannerError("AL1 scanner timed out") from error
    except OSError as error:
        raise AL1ScannerError(f"could not start AL1 scanner: {error}") from error

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown scanner error"
        raise AL1ScannerError(detail)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise AL1ScannerError("AL1 scanner returned invalid JSON") from error


def scan_summary(root: Path | None = None, scope: str | None = None) -> Any:
    return run_scanner(root, ["--summary"], scope)


def authority_index(root: Path | None = None, scope: str | None = None) -> Any:
    return run_scanner(root, ["--authority"], scope)


def resolve_component(query: str, root: Path | None = None, scope: str | None = None) -> Any:
    return run_scanner(root, ["--resolve", query], scope)


def component_impact(component_id: str, root: Path | None = None, scope: str | None = None) -> Any:
    return run_scanner(root, ["--impact", component_id], scope)


def tier_closure(component_id: str, root: Path | None = None, scope: str | None = None) -> Any:
    return run_scanner(root, ["--closure", component_id], scope)


def verify_rollback(component_id: str, root: Path | None = None, scope: str | None = None) -> Any:
    return run_scanner(root, ["--verify-rollback", component_id], scope)


def validate_promotion(
    component_id: str,
    evidence: str,
    root: Path | None = None,
    scope: str | None = None,
) -> Any:
    return run_scanner(
        root,
        ["--validate-promotion", component_id, "--evidence", evidence],
        scope,
    )
