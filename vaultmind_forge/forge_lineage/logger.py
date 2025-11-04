from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

class LineageLogger:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.accepted_dir = root / "lineage_logs" / "accepted"
        self.rejected_dir = root / "lineage_logs" / "rejected"
        self.archives_dir = root / "lineage_logs" / "archives"
        self.diagnostics_dir = root / "lineage_logs" / "diagnostics"
        for d in (self.accepted_dir, self.rejected_dir, self.archives_dir, self.diagnostics_dir):
            d.mkdir(parents=True, exist_ok=True)

    def write_report(self, job_id: str, pass_name: str, decision: str, report: Dict[str, Any]) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        base = self.accepted_dir if decision == "accept" else self.rejected_dir
        out = base / f"{job_id}__{pass_name}__{timestamp}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return out

    def write_diagnostics(self, job_id: str, pass_name: str, info: Dict[str, Any]) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        out = self.diagnostics_dir / f"{job_id}__{pass_name}__{timestamp}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        return out

    def finalize(self, job_id: str, bundle_paths: List[Path]) -> Path:
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        path = self.archives_dir / f"{job_id}__{stamp}.listing.txt"
        with open(path, "w", encoding="utf-8") as f:
            for p in bundle_paths:
                f.write(str(p) + "\n")
        return path