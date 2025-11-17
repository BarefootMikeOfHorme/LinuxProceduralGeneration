"""
VaultMind Forge - Batch Asset Ingestion
========================================

Processes hundreds of downloaded assets, extracting metadata, generating schemas,
and organizing into the asset library.
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
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import IntakeStage, QualityLevel, AssetCategory
from .multi_version_handler import MultiVersionHandler, process_with_multi_version
from .unified_converter import UnifiedConverter, ConversionStatus


@dataclass
class AssetMetadata:
    """Complete metadata for an ingested asset"""
    asset_id: str  # SHA256 hash
    filename: str
    original_path: str
    file_size: int
    file_type: str
    stage: str
    category: str
    quality: str
    timestamp: str

    # Archive contents (if applicable)
    is_archive: bool
    archive_contents: Optional[List[str]] = None
    extracted_formats: Optional[List[str]] = None

    # 3D Model metadata
    model_formats: Optional[List[str]] = None
    has_textures: bool = False
    has_materials: bool = False
    has_animations: bool = False
    has_rigging: bool = False

    # Detected characteristics
    inferred_type: Optional[str] = None
    inferred_category: Optional[str] = None
    polycount_estimate: Optional[str] = None

    # Tags for searchability
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class AssetIngestor:
    """Batch processes assets from Downloads into organized library"""

    # Supported formats
    ARCHIVE_FORMATS = {'.zip', '.rar', '.7z', '.tar', '.gz'}
    MODEL_FORMATS = {'.obj', '.fbx', '.gltf', '.glb', '.dae', '.blend',
                     '.c4d', '.ma', '.mb', '.max', '.3ds', '.stl', '.ply',
                     '.x3d', '.usd', '.usda', '.usdc'}
    TEXTURE_FORMATS = {'.png', '.jpg', '.jpeg', '.tga', '.bmp', '.tiff',
                       '.exr', '.hdr', '.dds', '.psd'}
    MATERIAL_FORMATS = {'.mtl', '.mat', '.materialx'}

    # Category detection keywords
    CATEGORY_KEYWORDS = {
        AssetCategory.CHARACTERS: ['character', 'human', 'person', 'avatar', 'mei', 'nathan', 'girl', 'boy', 'man', 'woman'],
        AssetCategory.VEHICLES: ['car', 'vehicle', 'mustang', 'bike', 'motorcycle', 'porsche', 'truck', 'ship', 'boat'],
        AssetCategory.WEAPONS: ['weapon', 'gun', 'sword', 'dagger', 'knife', 'rifle', 'blade'],
        AssetCategory.BUILDINGS: ['building', 'house', 'cottage', 'tower', 'structure'],
        AssetCategory.NATURE: ['tree', 'plant', 'flower', 'forest', 'landscape', 'mountain'],
        AssetCategory.PROPS: ['prop', 'bottle', 'can', 'soda', 'wine', 'donut', 'furniture'],
        AssetCategory.ANIMALS: ['animal', 'wolf', 'creature', 'alien', 'beast'],
        AssetCategory.ARCHITECTURE: ['architecture', 'arch', 'column', 'wall'],
        AssetCategory.EFFECTS: ['effect', 'particle', 'fx', 'explosion'],
        AssetCategory.ENVIRONMENTS: ['environment', 'scene', 'landscape', 'terrain', 'world'],
    }

    def __init__(self, downloads_dir: str, project_root: str, use_multi_version: bool = True):
        self.downloads_dir = Path(downloads_dir)
        self.project_root = Path(project_root)
        self.use_multi_version = use_multi_version

        # Key directories
        self.assets_dir = self.project_root / "assets"
        self.input_dir = self.assets_dir / "input"
        self.archive_dir = self.assets_dir / "archive"
        self.metadata_dir = self.assets_dir / "metadata"
        self.lineage_dir = self.assets_dir / "lineage"
        self.vaf_full_dir = self.assets_dir / "vaf_full"
        self.vaf_catalog_dir = self.assets_dir / "catalog"

        # Ensure directories exist
        for d in [self.input_dir, self.archive_dir, self.metadata_dir, self.lineage_dir,
                  self.vaf_full_dir, self.vaf_catalog_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Multi-version handler
        self.mv_handler = MultiVersionHandler() if use_multi_version else None
        self.converter = UnifiedConverter()

        self.processed_count = 0
        self.error_count = 0
        self.errors = []
        self.merged_count = 0

    def compute_hash(self, filepath: Path) -> str:
        """Compute SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def detect_category(self, filename: str, contents: List[str] = None) -> AssetCategory:
        """Infer asset category from filename and contents"""
        filename_lower = filename.lower()

        # Check filename against keywords
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in filename_lower for keyword in keywords):
                return category

        # Check archive contents if available
        if contents:
            contents_text = ' '.join(contents).lower()
            for category, keywords in self.CATEGORY_KEYWORDS.items():
                if any(keyword in contents_text for keyword in keywords):
                    return category

        return AssetCategory.UNCATEGORIZED

    def analyze_archive_contents(self, filepath: Path) -> Tuple[List[str], Dict[str, int]]:
        """Extract list of files and format statistics from archive"""
        contents = []
        format_counts = {}

        try:
            if filepath.suffix == '.zip':
                with zipfile.ZipFile(filepath, 'r') as zf:
                    contents = zf.namelist()
            elif filepath.suffix == '.rar':
                with rarfile.RarFile(filepath, 'r') as rf:
                    contents = rf.namelist()
            else:
                # Unsupported archive type
                return [], {}

            # Count formats
            for item in contents:
                ext = Path(item).suffix.lower()
                if ext:
                    format_counts[ext] = format_counts.get(ext, 0) + 1

            return contents, format_counts

        except Exception as e:
            print(f"Warning: Could not read archive {filepath.name}: {e}")
            return [], {}

    def extract_archive(self, filepath: Path, extract_to: Path) -> bool:
        """Extract archive to destination"""
        try:
            extract_to.mkdir(parents=True, exist_ok=True)

            if filepath.suffix == '.zip':
                with zipfile.ZipFile(filepath, 'r') as zf:
                    zf.extractall(extract_to)
            elif filepath.suffix == '.rar':
                with rarfile.RarFile(filepath, 'r') as rf:
                    rf.extractall(extract_to)
            else:
                return False

            return True

        except Exception as e:
            print(f"Error extracting {filepath.name}: {e}")
            return False

    def analyze_model_characteristics(self, formats: List[str], contents: List[str]) -> Dict:
        """Detect model characteristics from contents"""
        contents_lower = [c.lower() for c in contents]

        has_textures = any(
            any(c.endswith(ext) for ext in self.TEXTURE_FORMATS)
            for c in contents_lower
        )

        has_materials = any(
            any(c.endswith(ext) for ext in self.MATERIAL_FORMATS)
            for c in contents_lower
        )

        # Check for animation/rigging indicators
        has_animations = any(
            'anim' in c or 'walk' in c or 'run' in c or 'idle' in c
            for c in contents_lower
        )

        has_rigging = any(
            'rig' in c or 'skeleton' in c or 'bone' in c or 'armature' in c
            for c in contents_lower
        )

        return {
            'has_textures': has_textures,
            'has_materials': has_materials,
            'has_animations': has_animations,
            'has_rigging': has_rigging,
        }

    def generate_vaf_catalog(self, metadata: AssetMetadata) -> Dict:
        """Generate VAF-Catalog entry from asset metadata"""
        catalog = {
            "vaf_type": "catalog",
            "vaf_version": "1.0.0",
            "asset_id": metadata.asset_id,
            "name": Path(metadata.filename).stem.replace('_', ' ').replace('-', ' ').title(),
            "type": "model_3d" if metadata.model_formats else "unknown",
            "category": metadata.category,
            "tags": metadata.tags or [],
            "created": metadata.timestamp,
            "modified": metadata.timestamp,
            "stage": metadata.stage,
            "quality": metadata.quality,

            "statistics": {
                "materials": 1 if metadata.has_materials else 0,
                "textures": 1 if metadata.has_textures else 0,
                "animations": 1 if metadata.has_animations else 0,
                "bones": 1 if metadata.has_rigging else 0,
            },

            "capabilities": {
                "has_geometry": bool(metadata.model_formats),
                "has_materials": metadata.has_materials,
                "has_textures": metadata.has_textures,
                "has_rigging": metadata.has_rigging,
                "has_animations": metadata.has_animations,
                "has_lod": False,
            },

            "formats": {
                "source": {
                    "format": metadata.file_type,
                    "filename": metadata.filename,
                    "size_bytes": metadata.file_size,
                },
                "vaf_full": {
                    "available": False,  # Will be generated later
                    "path": None,
                },
            },

            "lineage": {
                "origin_hash": metadata.asset_id,
                "generation": 0,
            },
        }

        return catalog

    def generate_tags(self, filename: str, category: AssetCategory,
                     formats: List[str], characteristics: Dict) -> List[str]:
        """Generate semantic tags for asset"""
        tags = []

        # Add category
        tags.append(category.value)

        # Add formats
        tags.extend(formats)

        # Add characteristics
        if characteristics.get('has_textures'):
            tags.append('textured')
        if characteristics.get('has_materials'):
            tags.append('materials')
        if characteristics.get('has_animations'):
            tags.append('animated')
        if characteristics.get('has_rigging'):
            tags.append('rigged')

        # Add quality estimate (basic heuristic)
        if characteristics.get('has_rigging') and characteristics.get('has_textures'):
            tags.append('high-quality')
        elif characteristics.get('has_textures'):
            tags.append('medium-quality')
        else:
            tags.append('basic')

        # Add filename-based tags
        filename_lower = filename.lower().replace('-', ' ').replace('_', ' ')
        for word in filename_lower.split():
            if len(word) > 3 and word not in tags:
                tags.append(word)

        return tags

    def process_asset(self, filepath: Path) -> Optional[AssetMetadata]:
        """Process a single asset file"""
        try:
            # Skip non-files
            if not filepath.is_file():
                return None

            # Skip already processed (check if metadata exists)
            asset_id = self.compute_hash(filepath)
            metadata_path = self.metadata_dir / f"{asset_id}.json"
            if metadata_path.exists():
                print(f"[SKIP] Already processed: {filepath.name}")
                return None

            print(f"[>>] Processing: {filepath.name}")

            # Basic file info
            file_ext = filepath.suffix.lower()
            file_size = filepath.stat().st_size
            is_archive = file_ext in self.ARCHIVE_FORMATS

            # Initialize metadata
            metadata = AssetMetadata(
                asset_id=asset_id,
                filename=filepath.name,
                original_path=str(filepath),
                file_size=file_size,
                file_type=file_ext,
                stage=IntakeStage.RAW.value,
                category=AssetCategory.UNCATEGORIZED.value,
                quality=QualityLevel.UNKNOWN.value,
                timestamp=datetime.now().isoformat(),
                is_archive=is_archive,
            )

            # Process archives
            if is_archive:
                contents, format_counts = self.analyze_archive_contents(filepath)
                metadata.archive_contents = contents
                metadata.extracted_formats = list(format_counts.keys())

                # Detect model formats
                model_formats = [
                    fmt for fmt in format_counts.keys()
                    if fmt in self.MODEL_FORMATS
                ]
                metadata.model_formats = model_formats

                # Analyze characteristics
                if contents:
                    characteristics = self.analyze_model_characteristics(
                        model_formats, contents
                    )
                    metadata.has_textures = characteristics['has_textures']
                    metadata.has_materials = characteristics['has_materials']
                    metadata.has_animations = characteristics['has_animations']
                    metadata.has_rigging = characteristics['has_rigging']

                    # Detect category
                    category = self.detect_category(filepath.name, contents)
                    metadata.category = category.value

                    # Generate tags
                    metadata.tags = self.generate_tags(
                        filepath.name, category, metadata.extracted_formats, characteristics
                    )

                # Extract archive
                extract_dir = self.input_dir / filepath.stem
                if self.extract_archive(filepath, extract_dir):
                    metadata.stage = IntakeStage.EXTRACTED.value
                    print(f"  [+] Extracted to: {extract_dir.name}")

            # Direct model files (not in archive)
            elif file_ext in self.MODEL_FORMATS:
                metadata.model_formats = [file_ext]
                category = self.detect_category(filepath.name)
                metadata.category = category.value
                metadata.tags = [category.value, file_ext, '3d', 'model']

                # Copy to input
                dest = self.input_dir / filepath.name
                shutil.copy2(filepath, dest)
                metadata.stage = IntakeStage.EXTRACTED.value

            # Save metadata
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(metadata), f, indent=2)

            # Create lineage entry
            lineage_path = self.lineage_dir / f"{asset_id}.json"
            lineage = {
                "sha256": asset_id,
                "timestamp": metadata.timestamp,
                "operation": "intake",
                "generator": "forge_intake",
                "source": str(filepath),
                "category": metadata.category,
                "tags": metadata.tags,
            }
            with open(lineage_path, 'w', encoding='utf-8') as f:
                json.dump(lineage, f, indent=2)

            # Generate VAF-Catalog entry
            vaf_catalog = self.generate_vaf_catalog(metadata)
            vaf_catalog_path = self.metadata_dir / f"{asset_id}.vaf.catalog.json"
            with open(vaf_catalog_path, 'w', encoding='utf-8') as f:
                json.dump(vaf_catalog, f, indent=2)

            self.processed_count += 1
            print(f"  [OK] Metadata saved: {metadata_path.name}")
            print(f"  [OK] VAF-Catalog created: {vaf_catalog_path.name}")

            return metadata

        except Exception as e:
            self.error_count += 1
            error_msg = f"Error processing {filepath.name}: {e}"
            print(f"  [FAIL] {error_msg}")
            self.errors.append(error_msg)
            return None

    def scan_downloads(self) -> List[Path]:
        """Scan downloads directory for assets"""
        print(f"\n[*] Scanning: {self.downloads_dir}")

        all_files = []
        for item in self.downloads_dir.iterdir():
            if item.is_file():
                all_files.append(item)

        print(f"[+] Found {len(all_files)} files")
        return all_files

    def batch_process(self, max_workers: int = 4) -> Dict:
        """Process all assets in parallel"""
        files = self.scan_downloads()

        print(f"\n[*] Starting batch ingestion with {max_workers} workers...")
        print("=" * 60)

        results = []

        # Process in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.process_asset, f): f for f in files}

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        print("=" * 60)
        print(f"\n[+] Batch ingestion complete!")
        print(f"   Processed: {self.processed_count}")
        print(f"   Errors: {self.error_count}")

        if self.errors:
            print(f"\n[-] Errors encountered:")
            for error in self.errors[:10]:  # Show first 10
                print(f"   - {error}")
            if len(self.errors) > 10:
                print(f"   ... and {len(self.errors) - 10} more")

        # Generate summary report
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(files),
            "processed": self.processed_count,
            "errors": self.error_count,
            "error_details": self.errors,
        }

        summary_path = self.metadata_dir / "intake_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        print(f"\n[+] Summary saved to: {summary_path}")

        return summary


def main():
    """Run batch asset ingestion"""
    downloads = r"C:\Users\Administrator\Downloads"
    project = r"C:\Users\Administrator\Desktop\Projects\LPG"

    ingestor = AssetIngestor(downloads, project)
    summary = ingestor.batch_process(max_workers=4)

    return summary


if __name__ == "__main__":
    main()
