"""
VaultMind Forge - Multi-Version Asset Handler
==============================================

Handles assets that exist in multiple formats and intelligently merges them into
a unified VAF representation, selecting the best data from each source.

Example:
    robot_character.fbx   (has rigging + animations)
    robot_character.obj   (has high-poly geometry)
    robot_character.glb   (has optimized materials)
    robot_character.blend (has source editable data)

    → Merged into single VAF with best of all versions
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

from .format_registry import FormatRegistry, FormatSpec
from .unified_converter import UnifiedConverter, ConversionResult, ConversionStatus


@dataclass
class AssetVariant:
    """A single variant/version of an asset"""
    filepath: Path
    format: str
    priority: int  # From format registry
    asset_name: str  # Normalized name (without extension)
    group_key: str  # Key for grouping related variants


class MultiVersionHandler:
    """
    Detects and merges multiple format versions of the same asset.

    Strategy:
    1. Group files by normalized name (ignore format extensions)
    2. Convert each variant to intermediate representation
    3. Merge representations, prioritizing higher-quality data
    4. Generate unified VAF-Full from merged data
    """

    def __init__(self):
        self.registry = FormatRegistry()
        self.converter = UnifiedConverter()

    def normalize_asset_name(self, filename: str) -> str:
        """
        Normalize filename to find related variants.

        Examples:
            'robot_character.fbx' → 'robot_character'
            'robot-character_v2.obj' → 'robot_character'
            '10-rp_mei_posed_001_psd.zip' → 'rp_mei_posed_001'
        """
        # Remove extension
        name = Path(filename).stem

        # Remove common prefixes (numbers, hyphens)
        name = re.sub(r'^\d+-', '', name)  # Remove leading numbers like "10-"
        name = re.sub(r'^uploads_files_\d+_', '', name)  # Remove upload prefixes

        # Normalize separators
        name = name.replace('-', '_')
        name = name.lower()

        # Remove version suffixes
        name = re.sub(r'_v\d+$', '', name)
        name = re.sub(r'_\d{4}$', '', name)  # Remove year suffixes

        # Remove common suffixes
        suffixes_to_remove = [
            '_obj', '_fbx', '_gltf', '_blend', '_maya', '_c4d',
            '_texture', '_textures', '_compressed', '_animated',
            '_rigged', '_posed', '_walking', '_running'
        ]
        for suffix in suffixes_to_remove:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        return name.strip('_')

    def group_asset_variants(self, filepaths: List[Path]) -> Dict[str, List[AssetVariant]]:
        """
        Group files that are different versions of the same asset.

        Returns:
            Dict mapping normalized names to list of variants
        """
        groups = defaultdict(list)

        for filepath in filepaths:
            ext = filepath.suffix.lower()
            spec = self.registry.get_spec(ext)

            if not spec:
                continue  # Skip unsupported formats

            normalized_name = self.normalize_asset_name(filepath.name)

            variant = AssetVariant(
                filepath=filepath,
                format=ext,
                priority=spec.priority,
                asset_name=normalized_name,
                group_key=normalized_name,
            )

            groups[normalized_name].append(variant)

        return dict(groups)

    def select_primary_variant(self, variants: List[AssetVariant]) -> AssetVariant:
        """
        Select the primary/preferred variant based on format priority.

        Priority order (higher is better):
        - .gltf/.glb (100/95) - Modern standard
        - .fbx (90) - Industry standard
        - .usd (85) - High-end production
        - .dae (75) - Open standard
        - .obj (70) - Simple but universal
        - .blend (60) - Requires Blender
        """
        return max(variants, key=lambda v: v.priority)

    def merge_variants(
        self,
        variants: List[AssetVariant],
        asset_id: str
    ) -> ConversionResult:
        """
        Merge multiple format variants into a single unified VAF.

        Strategy:
        1. Select primary variant (best format)
        2. Extract data from all variants
        3. Merge data, preferring:
           - Geometry: Highest polycount (but reasonable)
           - Materials: Most complete PBR data
           - Rigging: Most detailed skeleton
           - Animations: Most animation clips
           - Textures: Highest resolution
        """

        if not variants:
            return ConversionResult(
                status=ConversionStatus.FAILED,
                errors=["No variants provided"]
            )

        # Sort by priority (highest first)
        variants_sorted = sorted(variants, key=lambda v: v.priority, reverse=True)

        # Convert all variants
        conversions: List[Tuple[AssetVariant, ConversionResult]] = []
        for variant in variants_sorted:
            result = self.converter.convert(variant.filepath, asset_id)
            conversions.append((variant, result))

        # Start with primary variant
        primary_variant, primary_result = conversions[0]

        if primary_result.status == ConversionStatus.FAILED:
            # Try next variant
            for variant, result in conversions[1:]:
                if result.status == ConversionStatus.SUCCESS:
                    primary_variant, primary_result = variant, result
                    break

        if not primary_result.vaf_full:
            return ConversionResult(
                status=ConversionStatus.FAILED,
                errors=["All conversions failed"]
            )

        # Merge data from other variants
        merged_vaf = primary_result.vaf_full.copy()
        merge_info = {
            "primary_format": primary_variant.format,
            "merged_formats": [],
            "merge_operations": [],
        }

        for variant, result in conversions[1:]:
            if result.status != ConversionStatus.SUCCESS or not result.vaf_full:
                continue

            # Merge geometry (if better)
            self._merge_geometry(merged_vaf, result.vaf_full, variant, merge_info)

            # Merge materials
            self._merge_materials(merged_vaf, result.vaf_full, variant, merge_info)

            # Merge rigging
            self._merge_rigging(merged_vaf, result.vaf_full, variant, merge_info)

            # Merge animations
            self._merge_animations(merged_vaf, result.vaf_full, variant, merge_info)

            merge_info["merged_formats"].append(variant.format)

        # Add merge metadata
        merged_vaf["metadata"]["multi_version"] = merge_info

        # Update lineage to reflect all source files
        merged_vaf["lineage"]["transformations"].append({
            "operation": "multi_version_merge",
            "source_formats": [v.format for v in variants_sorted],
            "primary_format": primary_variant.format,
        })

        # Regenerate catalog
        merged_catalog = self.converter._generate_catalog(
            merged_vaf,
            primary_variant.filepath
        )

        return ConversionResult(
            status=ConversionStatus.SUCCESS,
            vaf_full=merged_vaf,
            vaf_catalog=merged_catalog,
            warnings=[f"Merged {len(variants)} format variants"]
        )

    def _merge_geometry(
        self,
        target: Dict,
        source: Dict,
        variant: AssetVariant,
        merge_info: Dict
    ):
        """Merge geometry data, preferring higher quality"""
        target_geo = target.get("geometry", {})
        source_geo = source.get("geometry", {})

        target_stats = target_geo.get("statistics", {})
        source_stats = source_geo.get("statistics", {})

        target_verts = target_stats.get("total_vertices", 0)
        source_verts = source_stats.get("total_vertices", 0)

        # Prefer source if it has more vertices (up to a reasonable limit)
        if source_verts > target_verts and source_verts < target_verts * 5:
            target["geometry"] = source_geo
            merge_info["merge_operations"].append(
                f"Used geometry from {variant.format} ({source_verts} verts)"
            )

        # Merge additional vertex attributes
        if source_stats.get("has_normals") and not target_stats.get("has_normals"):
            target_stats["has_normals"] = True
            merge_info["merge_operations"].append(
                f"Added normals from {variant.format}"
            )

        if source_stats.get("has_uvs") and not target_stats.get("has_uvs"):
            target_stats["has_uvs"] = True
            merge_info["merge_operations"].append(
                f"Added UVs from {variant.format}"
            )

    def _merge_materials(
        self,
        target: Dict,
        source: Dict,
        variant: AssetVariant,
        merge_info: Dict
    ):
        """Merge material definitions"""
        target_mats = target.get("materials", {})
        source_mats = source.get("materials", {})

        # If source has more materials, use them
        source_mat_count = len(source_mats.get("definitions", []))
        target_mat_count = len(target_mats.get("definitions", []))

        if source_mat_count > target_mat_count:
            target["materials"]["definitions"] = source_mats.get("definitions", [])
            merge_info["merge_operations"].append(
                f"Used materials from {variant.format} ({source_mat_count} materials)"
            )

        # Merge textures (combine unique textures)
        source_textures = source_mats.get("textures", [])
        target_textures = target_mats.get("textures", [])

        if source_textures:
            # Add unique textures
            existing_names = {t.get("name") for t in target_textures}
            new_textures = [
                t for t in source_textures
                if t.get("name") not in existing_names
            ]
            if new_textures:
                target_textures.extend(new_textures)
                target["materials"]["textures"] = target_textures
                merge_info["merge_operations"].append(
                    f"Added {len(new_textures)} textures from {variant.format}"
                )

    def _merge_rigging(
        self,
        target: Dict,
        source: Dict,
        variant: AssetVariant,
        merge_info: Dict
    ):
        """Merge rigging/skeleton data"""
        target_rig = target.get("rigging", {})
        source_rig = source.get("rigging", {})

        # If source has rigging and target doesn't, use it
        if source_rig and not target_rig:
            target["rigging"] = source_rig
            merge_info["merge_operations"].append(
                f"Added rigging from {variant.format}"
            )
        # If source has more bones, prefer it
        elif source_rig and target_rig:
            source_bones = len(source_rig.get("skeleton", {}).get("bones", []))
            target_bones = len(target_rig.get("skeleton", {}).get("bones", []))

            if source_bones > target_bones:
                target["rigging"] = source_rig
                merge_info["merge_operations"].append(
                    f"Used rigging from {variant.format} ({source_bones} bones)"
                )

    def _merge_animations(
        self,
        target: Dict,
        source: Dict,
        variant: AssetVariant,
        merge_info: Dict
    ):
        """Merge animation clips"""
        target_anims = target.get("animations", [])
        source_anims = source.get("animations", [])

        if not source_anims:
            return

        # Add unique animations
        existing_names = {a.get("name") for a in target_anims}
        new_anims = [
            a for a in source_anims
            if a.get("name") not in existing_names
        ]

        if new_anims:
            target_anims.extend(new_anims)
            target["animations"] = target_anims
            merge_info["merge_operations"].append(
                f"Added {len(new_anims)} animations from {variant.format}"
            )


# =============================================================================
# Batch Processing with Multi-Version Support
# =============================================================================

def process_with_multi_version(
    filepaths: List[Path],
    asset_id_map: Dict[Path, str]
) -> Dict[str, ConversionResult]:
    """
    Process files with multi-version detection and merging.

    Args:
        filepaths: List of all files to process
        asset_id_map: Mapping of filepath to asset ID

    Returns:
        Dict mapping asset name to ConversionResult
    """
    handler = MultiVersionHandler()

    # Group by asset name
    groups = handler.group_asset_variants(filepaths)

    results = {}

    for asset_name, variants in groups.items():
        print(f"[*] Processing asset: {asset_name} ({len(variants)} variants)")

        # Get asset ID (use primary variant's ID)
        primary = handler.select_primary_variant(variants)
        asset_id = asset_id_map.get(primary.filepath, asset_name)

        # Merge variants
        result = handler.merge_variants(variants, asset_id)

        results[asset_name] = result

        if result.status == ConversionStatus.SUCCESS:
            print(f"  [+] Success! Merged {len(variants)} formats")
            for warning in result.warnings:
                print(f"  [WARN] {warning}")
        else:
            print(f"  [ERROR] Failed: {result.errors}")

    return results
