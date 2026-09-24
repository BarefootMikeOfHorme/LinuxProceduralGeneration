"""Isolated worker process for structured build123d plans.

The worker accepts JSON plans only. Arbitrary user-authored build123d source
is intentionally not supported by this entry point; it must be handled by a
future separately sandboxed source worker.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .build123d_ai import execute_plan, plan_from_dict
from .contracts import ConversionEnvelope, ConversionLossStatus


def _failed_envelope(message: str, *, job_id: str = "") -> ConversionEnvelope:
    return ConversionEnvelope(
        asset_id=job_id,
        source_format="build123d-plan",
        target_format="step,stl",
        loss_status=ConversionLossStatus.FAILED,
        errors=[message],
        provenance={
            "tool": "build123d",
            "operation": "isolated_structured_plan",
        },
    )


def run_worker(job_path: str, result_path: str) -> int:
    """Worker entry point invoked as ``python -m ... job.json result.json``."""
    job_id = ""
    try:
        job = json.loads(Path(job_path).read_text(encoding="utf-8"))
        if not isinstance(job, Mapping):
            raise ValueError("worker job must be a JSON object")
        job_id = str(job.get("job_id", ""))
        plan = job.get("plan")
        output_dir = Path(str(job["output_dir"]))
        result = execute_plan(plan_from_dict(plan), output_dir)
    except Exception as error:
        result = _failed_envelope(f"build123d worker failed: {error}", job_id=job_id)

    result_path_obj = Path(result_path)
    result_path_obj.parent.mkdir(parents=True, exist_ok=True)
    result_path_obj.write_text(
        json.dumps(result.to_dict(), indent=2),
        encoding="utf-8",
    )
    return 0 if result.loss_status != ConversionLossStatus.FAILED else 2


def execute_isolated_plan(
    plan: Mapping[str, Any],
    output_dir: str | Path,
    timeout_seconds: int = 60,
) -> ConversionEnvelope:
    """Run a structured plan in a child process and return its envelope."""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")

    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    job_id = f"build123d-{uuid.uuid4().hex[:12]}"
    job_dir = Path(tempfile.mkdtemp(prefix="lpg-build123d-job-"))
    job_path = job_dir / "job.json"
    result_path = job_dir / "result.json"
    job = {
        "schema_version": "1.0",
        "job_id": job_id,
        "plan": dict(plan),
        "output_dir": str(output_path),
    }

    try:
        job_path.write_text(json.dumps(job, indent=2), encoding="utf-8")
        package_root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = os.pathsep.join(
            item for item in (str(package_root), existing_pythonpath) if item
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "vaultmind_forge.forge_converter.build123d_worker",
                str(job_path),
                str(result_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            env=env,
        )
        if not result_path.is_file():
            detail = (completed.stderr or completed.stdout or "worker produced no result").strip()
            return _failed_envelope(
                f"build123d worker exited {completed.returncode}: {detail[-1000:]}",
                job_id=job_id,
            )
        return ConversionEnvelope.from_dict(
            json.loads(result_path.read_text(encoding="utf-8"))
        )
    except subprocess.TimeoutExpired:
        return _failed_envelope(
            f"build123d worker timed out after {timeout_seconds} seconds",
            job_id=job_id,
        )
    except Exception as error:
        return _failed_envelope(f"build123d worker launch failed: {error}", job_id=job_id)
    finally:
        shutil.rmtree(job_dir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: build123d_worker JOB_JSON RESULT_JSON", file=sys.stderr)
        raise SystemExit(64)
    raise SystemExit(run_worker(sys.argv[1], sys.argv[2]))
