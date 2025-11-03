from pathlib import Path
import zipfile
import json
from typing import List

class Packager:
 def package_assets(self, assets: List[Path], out_zip: Path | str, metadata: dict = None) -> Path:
 out_zip = Path(out_zip)
 out_zip.parent.mkdir(parents=True, exist_ok=True)
 with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
 for a in assets:
 z.write(a, arcname=a.name)
 # write metadata as a JSON file inside the zip
 meta = metadata or {}
 meta_bytes = json.dumps(meta, indent=2).encode("utf-8")
 z.writestr("metadata.json", meta_bytes)
 return out_zip
