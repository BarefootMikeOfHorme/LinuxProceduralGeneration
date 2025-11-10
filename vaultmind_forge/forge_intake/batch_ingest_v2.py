"""
VaultMind Forge - Batch Asset Ingestion V2
===========================================

Enhanced version with multi-version asset support and unified VAF conversion.
"""

import os
import json
import hashlib
import zipfile
import rarfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import IntakeStage, QualityLevel, AssetCategory
from .multi_version_handler import MultiVersionHandler, process_with_multi_version
from .unified_converter import UnifiedConverter, ConversionStatus


class AssetIngestorV2:
    """Enhanced asset ingestor with multi-version support"""

    def __init__(self, downloads_dir: str, project_root: str):
        self.downloads_dir = Path(downloads_dir)
        self.project_root = Path(project_root)

        # Directories
        self.assets_dir = self.project_root / "assets"
        self.input_dir = self.assets_dir / "input"
        self.vaf_full_dir = self.assets_dir / "vaf_full"
        self.vaf_catalog_dir = self.assets_dir / "catalog"
        self.metadata_dir = self.assets_dir / "metadata"
        self.lineage_dir = self.assets_dir / "lineage"

        for d in [self.input_dir, self.vaf_full_dir, self.vaf_catalog_dir,
                  self.metadata_dir, self.lineage_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Handlers
        self.mv_handler = MultiVersionHandler()
        self.converter = UnifiedConverter()

        # Stats
        self.processed_assets = 0
        self.merged_variants = 0
        self.total_files = 0
        self.errors = []

    def compute_hash(self, filepath: Path) -> str:
        """Compute SHA256 hash"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def extract_archives(self, filepaths: List[Path]) -> List[Path]:
        """Extract all archives and return list of extracted files"""
        extracted_files = []

        for filepath in filepaths:
            ext = filepath.suffix.lower()

            if ext in ['.zip', '.rar']:
                try:
                    print(f"[*] Extracting: {filepath.name}")
                    extract_dir = self.input_dir / filepath.stem

                    if ext == '.zip':
                        with zipfile.ZipFile(filepath, 'r') as zf:
                            zf.extractall(extract_dir)
                    elif ext == '.rar':
                        with rarfile.RarFile(filepath, 'r') as rf:
                            rf.extractall(extract_dir)

                    # Add extracted files to list
                    for root, dirs, files in os.walk(extract_dir):
                        for file in files:
                            extracted_files.append(Path(root) / file)

                    print(f"  [+] Extracted {len(list(extract_dir.rglob('*')))} items")

                except Exception as e:
                    print(f"  [ERROR] Failed to extract: {e}")
                    self.errors.append(f"Extract failed {filepath.name}: {e}")

            else:
                # Not an archive, just copy to input
                dest = self.input_dir / filepath.name
                if not dest.exists():
                    shutil.copy2(filepath, dest)
                extracted_files.append(dest)

        return extracted_files

    def batch_process(self, max_workers: int = 4) -> Dict:
        """Process all assets with multi-version support"""
        print("[*] VaultMind Forge - Batch Asset Ingestion V2")
        print("=" * 60)

        # Step 1: Scan downloads
        print(f"\n[*] Scanning: {self.downloads_dir}")
        all_files = list(self.downloads_dir.iterdir())
        all_files = [f for f in all_files if f.is_file()]
        self.total_files = len(all_files)
        print(f"[+] Found {self.total_files} files")

        # Step 2: Extract archives
        print(f"\n[*] Extracting archives...")
        extracted_files = self.extract_archives(all_files)
        print(f"[+] Total files after extraction: {len(extracted_files)}")

        # Step 3: Compute hashes for all files
        print(f"\n[*] Computing file hashes...")
        asset_id_map = {}
        for filepath in extracted_files:
            if filepath.is_file():
                try:
                    asset_id = self.compute_hash(filepath)
                    asset_id_map[filepath] = asset_id
                except:
                    pass
        print(f"[+] Hashed {len(asset_id_map)} files")

        # Step 4: Group and merge multi-version assets
        print(f"\n[*] Detecting and grouping asset variants...")
        groups = self.mv_handler.group_asset_variants(list(asset_id_map.keys()))
        print(f"[+] Found {len(groups)} unique assets")

        multi_version_assets = {
            name: variants
            for name, variants in groups.items()
            if len(variants) > 1
        }
        print(f"[+] {len(multi_version_assets)} assets have multiple format versions")

        # Step 5: Process assets
        print(f"\n[*] Converting assets to VAF...")
        print("=" * 60)

        for asset_name, variants in groups.items():
            try:
                print(f"\n[>>] {asset_name} ({len(variants)} variants)")

                # Get asset ID from primary variant
                primary = self.mv_handler.select_primary_variant(variants)
                asset_id = asset_id_map[primary.filepath]

                # Merge variants
                result = self.mv_handler.merge_variants(variants, asset_id)

                if result.status == ConversionStatus.SUCCESS:
                    # Save VAF-Full
                    vaf_full_path = self.vaf_full_dir / f"{asset_id}.vaf.full.json"
                    with open(vaf_full_path, 'w', encoding='utf-8') as f:
                        json.dump(result.vaf_full, f, indent=2)

                    # Save VAF-Catalog
                    vaf_catalog_path = self.vaf_catalog_dir / f"{asset_id}.vaf.catalog.json"
                    with open(vaf_catalog_path, 'w', encoding='utf-8') as f:
                        json.dump(result.vaf_catalog, f, indent=2)

                    # Save lineage
                    lineage_path = self.lineage_dir / f"{asset_id}.json"
                    lineage = result.vaf_full.get("lineage", {})
                    with open(lineage_path, 'w', encoding='utf-8') as f:
                        json.dump(lineage, f, indent=2)

                    self.processed_assets += 1
                    if len(variants) > 1:
                        self.merged_variants += 1

                    print(f"  [+] Converted to VAF")
                    if len(variants) > 1:
                        print(f"  [+] Merged {len(variants)} format versions:")
                        for v in variants:
                            print(f"      - {v.format:8} (priority: {v.priority})")

                else:
                    print(f"  [ERROR] Conversion failed: {result.errors}")
                    self.errors.append(f"{asset_name}: {result.errors}")

            except Exception as e:
                print(f"  [ERROR] Processing failed: {e}")
                self.errors.append(f"{asset_name}: {str(e)}")

        # Step 6: Generate summary
        print("\n" + "=" * 60)
        print(f"[+] Batch ingestion complete!")
        print(f"    Total input files: {self.total_files}")
        print(f"    Unique assets: {len(groups)}")
        print(f"    Successfully processed: {self.processed_assets}")
        print(f"    Multi-version merges: {self.merged_variants}")
        print(f"    Errors: {len(self.errors)}")

        if self.errors:
            print(f"\n[-] Errors encountered:")
            for error in self.errors[:10]:
                print(f"    - {error}")
            if len(self.errors) > 10:
                print(f"    ... and {len(self.errors) - 10} more")

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_input_files": self.total_files,
            "unique_assets": len(groups),
            "processed": self.processed_assets,
            "multi_version_merges": self.merged_variants,
            "errors": len(self.errors),
            "error_details": self.errors,
        }

        summary_path = self.metadata_dir / "ingestion_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        print(f"\n[+] Summary saved to: {summary_path}")

        return summary


def main():
    """Run batch asset ingestion V2"""
    downloads = r"C:\Users\Administrator\Downloads"
    project = r"C:\Users\Administrator\Desktop\Projects\LPG"

    ingestor = AssetIngestorV2(downloads, project)
    summary = ingestor.batch_process(max_workers=4)

    return summary


if __name__ == "__main__":
    main()
