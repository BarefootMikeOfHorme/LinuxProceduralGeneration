from pathlib import Path
import json
from datetime import datetime
from typing import List

class LineageStore:
 def __init__(self, root: Path | str):
 self.root = Path(root)
 self.root.mkdir(parents=True, exist_ok=True)

 def record_run(self, job, assets: List[Path], validations: list, package: str | None = None):
 entry = {
 "timestamp": datetime.utcnow().isoformat() + "Z",
 "job": job.__dict__ if hasattr(job, "__dict__") else job,
 "assets": [str(a) for a in assets],
 "validations": [v.model_dump() if hasattr(v, "model_dump") else v.__dict__ for v in validations],
 "package": package
 }
 nid = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
 p = self.root / f"run_{nid}.json"
 p.write_text(json.dumps(entry, indent=2))
 return p
