"""
VaultMind Forge - Comprehensive Output Structure
Defines all output endpoints for every media type and format
"""

from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class OutputStructure:
    """
    Comprehensive output folder structure for ALL media types

    Covers:
    - Procedural generation (textures, heightmaps, noise patterns)
    - 2D assets (images, sprites, UI elements)
    - 3D assets (meshes, models, materials)
    - Audio (music, SFX, ambient, voice)
    - Video (cutscenes, trailers, animations)
    - Game environments (levels, terrains, biomes)
    - Special formats (VFX, shaders, particles)
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize output structure

        Args:
            base_path: Root directory for all outputs (defaults to project assets)
        """
        if base_path is None:
            base_path = Path(__file__).parents[2] / "assets"

        self.base_path = Path(base_path)

        # Define COMPREHENSIVE output structure
        self.structure = {
            # ================================================================
            # PROCEDURAL GENERATION OUTPUTS
            # ================================================================
            'procedural': {
                # Noise patterns and textures
                'noise': {
                    'perlin': self.base_path / "procedural" / "noise" / "perlin",
                    'simplex': self.base_path / "procedural" / "noise" / "simplex",
                    'worley': self.base_path / "procedural" / "noise" / "worley",
                    'voronoi': self.base_path / "procedural" / "noise" / "voronoi",
                    'fbm': self.base_path / "procedural" / "noise" / "fbm",
                    'cellular': self.base_path / "procedural" / "noise" / "cellular",
                },
                # Texture types
                'textures': {
                    'clouds': self.base_path / "procedural" / "textures" / "clouds",
                    'marble': self.base_path / "procedural" / "textures" / "marble",
                    'wood': self.base_path / "procedural" / "textures" / "wood",
                    'stone': self.base_path / "procedural" / "textures" / "stone",
                    'metal': self.base_path / "procedural" / "textures" / "metal",
                    'organic': self.base_path / "procedural" / "textures" / "organic",
                    'water': self.base_path / "procedural" / "textures" / "water",
                    'fire': self.base_path / "procedural" / "textures" / "fire",
                    'smoke': self.base_path / "procedural" / "textures" / "smoke",
                    'plasma': self.base_path / "procedural" / "textures" / "plasma",
                },
                # Terrain and heightmaps
                'terrain': {
                    'heightmaps': self.base_path / "procedural" / "terrain" / "heightmaps",
                    'mountains': self.base_path / "procedural" / "terrain" / "mountains",
                    'hills': self.base_path / "procedural" / "terrain" / "hills",
                    'plains': self.base_path / "procedural" / "terrain" / "plains",
                    'valleys': self.base_path / "procedural" / "terrain" / "valleys",
                    'canyons': self.base_path / "procedural" / "terrain" / "canyons",
                    'islands': self.base_path / "procedural" / "terrain" / "islands",
                    'continents': self.base_path / "procedural" / "terrain" / "continents",
                },
                # Patterns
                'patterns': {
                    'geometric': self.base_path / "procedural" / "patterns" / "geometric",
                    'fractals': self.base_path / "procedural" / "patterns" / "fractals",
                    'organic': self.base_path / "procedural" / "patterns" / "organic",
                    'abstract': self.base_path / "procedural" / "patterns" / "abstract",
                },
            },

            # ================================================================
            # 2D ASSETS
            # ================================================================
            '2d': {
                # Images
                'images': {
                    'png': self.base_path / "2d" / "images" / "png",
                    'jpg': self.base_path / "2d" / "images" / "jpg",
                    'tga': self.base_path / "2d" / "images" / "tga",
                    'bmp': self.base_path / "2d" / "images" / "bmp",
                    'webp': self.base_path / "2d" / "images" / "webp",
                    'exr': self.base_path / "2d" / "images" / "exr",  # HDR
                    'hdr': self.base_path / "2d" / "images" / "hdr",
                },
                # Textures
                'textures': {
                    'diffuse': self.base_path / "2d" / "textures" / "diffuse",
                    'normal': self.base_path / "2d" / "textures" / "normal",
                    'roughness': self.base_path / "2d" / "textures" / "roughness",
                    'metallic': self.base_path / "2d" / "textures" / "metallic",
                    'ao': self.base_path / "2d" / "textures" / "ao",  # Ambient Occlusion
                    'displacement': self.base_path / "2d" / "textures" / "displacement",
                    'emissive': self.base_path / "2d" / "textures" / "emissive",
                    'opacity': self.base_path / "2d" / "textures" / "opacity",
                },
                # Sprites
                'sprites': {
                    'characters': self.base_path / "2d" / "sprites" / "characters",
                    'items': self.base_path / "2d" / "sprites" / "items",
                    'ui': self.base_path / "2d" / "sprites" / "ui",
                    'effects': self.base_path / "2d" / "sprites" / "effects",
                    'tiles': self.base_path / "2d" / "sprites" / "tiles",
                },
                # UI Elements
                'ui': {
                    'buttons': self.base_path / "2d" / "ui" / "buttons",
                    'icons': self.base_path / "2d" / "ui" / "icons",
                    'panels': self.base_path / "2d" / "ui" / "panels",
                    'fonts': self.base_path / "2d" / "ui" / "fonts",
                    'cursors': self.base_path / "2d" / "ui" / "cursors",
                },
            },

            # ================================================================
            # 3D ASSETS
            # ================================================================
            '3d': {
                # Mesh formats
                'meshes': {
                    'obj': self.base_path / "3d" / "meshes" / "obj",
                    'fbx': self.base_path / "3d" / "meshes" / "fbx",
                    'gltf': self.base_path / "3d" / "meshes" / "gltf",
                    'glb': self.base_path / "3d" / "meshes" / "glb",
                    'dae': self.base_path / "3d" / "meshes" / "dae",  # Collada
                    'stl': self.base_path / "3d" / "meshes" / "stl",
                    'ply': self.base_path / "3d" / "meshes" / "ply",
                    'blend': self.base_path / "3d" / "meshes" / "blend",  # Blender
                    'usd': self.base_path / "3d" / "meshes" / "usd",  # Universal Scene Description
                },
                # Model categories
                'models': {
                    'characters': self.base_path / "3d" / "models" / "characters",
                    'props': self.base_path / "3d" / "models" / "props",
                    'weapons': self.base_path / "3d" / "models" / "weapons",
                    'vehicles': self.base_path / "3d" / "models" / "vehicles",
                    'buildings': self.base_path / "3d" / "models" / "buildings",
                    'nature': self.base_path / "3d" / "models" / "nature",
                    'furniture': self.base_path / "3d" / "models" / "furniture",
                    'architecture': self.base_path / "3d" / "models" / "architecture",
                },
                # Materials
                'materials': {
                    'pbr': self.base_path / "3d" / "materials" / "pbr",
                    'procedural': self.base_path / "3d" / "materials" / "procedural",
                    'shader': self.base_path / "3d" / "materials" / "shader",
                    'substance': self.base_path / "3d" / "materials" / "substance",
                },
                # Animations
                'animations': {
                    'skeletal': self.base_path / "3d" / "animations" / "skeletal",
                    'morph': self.base_path / "3d" / "animations" / "morph",
                    'procedural': self.base_path / "3d" / "animations" / "procedural",
                    'mocap': self.base_path / "3d" / "animations" / "mocap",
                },
            },

            # ================================================================
            # AUDIO ASSETS
            # ================================================================
            'audio': {
                # Music
                'music': {
                    'ambient': self.base_path / "audio" / "music" / "ambient",
                    'combat': self.base_path / "audio" / "music" / "combat",
                    'menu': self.base_path / "audio" / "music" / "menu",
                    'cinematic': self.base_path / "audio" / "music" / "cinematic",
                    'loops': self.base_path / "audio" / "music" / "loops",
                },
                # Sound effects
                'sfx': {
                    'ui': self.base_path / "audio" / "sfx" / "ui",
                    'footsteps': self.base_path / "audio" / "sfx" / "footsteps",
                    'weapons': self.base_path / "audio" / "sfx" / "weapons",
                    'impacts': self.base_path / "audio" / "sfx" / "impacts",
                    'environment': self.base_path / "audio" / "sfx" / "environment",
                    'magic': self.base_path / "audio" / "sfx" / "magic",
                },
                # Voice
                'voice': {
                    'dialogue': self.base_path / "audio" / "voice" / "dialogue",
                    'narration': self.base_path / "audio" / "voice" / "narration",
                    'barks': self.base_path / "audio" / "voice" / "barks",  # Short reactions
                },
                # Formats
                'formats': {
                    'wav': self.base_path / "audio" / "formats" / "wav",
                    'mp3': self.base_path / "audio" / "formats" / "mp3",
                    'ogg': self.base_path / "audio" / "formats" / "ogg",
                    'flac': self.base_path / "audio" / "formats" / "flac",
                },
            },

            # ================================================================
            # VIDEO ASSETS
            # ================================================================
            'video': {
                # Video types
                'cutscenes': self.base_path / "video" / "cutscenes",
                'trailers': self.base_path / "video" / "trailers",
                'tutorials': self.base_path / "video" / "tutorials",
                'backgrounds': self.base_path / "video" / "backgrounds",
                # Formats
                'formats': {
                    'mp4': self.base_path / "video" / "formats" / "mp4",
                    'webm': self.base_path / "video" / "formats" / "webm",
                    'mov': self.base_path / "video" / "formats" / "mov",
                    'avi': self.base_path / "video" / "formats" / "avi",
                },
            },

            # ================================================================
            # GAME ENVIRONMENTS
            # ================================================================
            'environments': {
                # Biomes
                'biomes': {
                    'forest': self.base_path / "environments" / "biomes" / "forest",
                    'desert': self.base_path / "environments" / "biomes" / "desert",
                    'tundra': self.base_path / "environments" / "biomes" / "tundra",
                    'ocean': self.base_path / "environments" / "biomes" / "ocean",
                    'mountains': self.base_path / "environments" / "biomes" / "mountains",
                    'jungle': self.base_path / "environments" / "biomes" / "jungle",
                    'urban': self.base_path / "environments" / "biomes" / "urban",
                    'alien': self.base_path / "environments" / "biomes" / "alien",
                },
                # Levels
                'levels': {
                    'interior': self.base_path / "environments" / "levels" / "interior",
                    'exterior': self.base_path / "environments" / "levels" / "exterior",
                    'dungeons': self.base_path / "environments" / "levels" / "dungeons",
                    'arenas': self.base_path / "environments" / "levels" / "arenas",
                },
                # Skyboxes
                'skyboxes': {
                    'day': self.base_path / "environments" / "skyboxes" / "day",
                    'night': self.base_path / "environments" / "skyboxes" / "night",
                    'space': self.base_path / "environments" / "skyboxes" / "space",
                    'fantasy': self.base_path / "environments" / "skyboxes" / "fantasy",
                },
            },

            # ================================================================
            # SPECIAL FORMATS
            # ================================================================
            'special': {
                # VFX
                'vfx': {
                    'particles': self.base_path / "special" / "vfx" / "particles",
                    'explosions': self.base_path / "special" / "vfx" / "explosions",
                    'magic': self.base_path / "special" / "vfx" / "magic",
                    'weather': self.base_path / "special" / "vfx" / "weather",
                    'trails': self.base_path / "special" / "vfx" / "trails",
                },
                # Shaders
                'shaders': {
                    'hlsl': self.base_path / "special" / "shaders" / "hlsl",
                    'glsl': self.base_path / "special" / "shaders" / "glsl",
                    'shadergraph': self.base_path / "special" / "shaders" / "shadergraph",
                    'amplify': self.base_path / "special" / "shaders" / "amplify",
                },
                # Lighting
                'lighting': {
                    'lightmaps': self.base_path / "special" / "lighting" / "lightmaps",
                    'probes': self.base_path / "special" / "lighting" / "probes",
                    'hdri': self.base_path / "special" / "lighting" / "hdri",
                },
            },

            # ================================================================
            # ENGINE-SPECIFIC OUTPUTS
            # ================================================================
            'engines': {
                'unity': {
                    'packages': self.base_path / "engines" / "unity" / "packages",
                    'prefabs': self.base_path / "engines" / "unity" / "prefabs",
                    'scenes': self.base_path / "engines" / "unity" / "scenes",
                    'materials': self.base_path / "engines" / "unity" / "materials",
                },
                'unreal': {
                    'packages': self.base_path / "engines" / "unreal" / "packages",
                    'blueprints': self.base_path / "engines" / "unreal" / "blueprints",
                    'levels': self.base_path / "engines" / "unreal" / "levels",
                    'materials': self.base_path / "engines" / "unreal" / "materials",
                },
                'godot': {
                    'scenes': self.base_path / "engines" / "godot" / "scenes",
                    'resources': self.base_path / "engines" / "godot" / "resources",
                    'materials': self.base_path / "engines" / "godot" / "materials",
                },
                'blender': {
                    'projects': self.base_path / "engines" / "blender" / "projects",
                    'exports': self.base_path / "engines" / "blender" / "exports",
                },
                'web': {
                    'threejs': self.base_path / "engines" / "web" / "threejs",
                    'babylonjs': self.base_path / "engines" / "web" / "babylonjs",
                    'webgl': self.base_path / "engines" / "web" / "webgl",
                },
            },

            # ================================================================
            # VALIDATION & PIPELINE
            # ================================================================
            'validated': {
                'winners': self.base_path / "validated" / "winners",
                'rejected': self.base_path / "validated" / "rejected",
                'flagged': self.base_path / "validated" / "flagged_for_review",
                'pending': self.base_path / "validated" / "pending",
            },

            # ================================================================
            # PACKAGING & DISTRIBUTION
            # ================================================================
            'packages': {
                'asset_packs': self.base_path / "packages" / "asset_packs",
                'archives': self.base_path / "packages" / "archives",
                'distribution': self.base_path / "packages" / "distribution",
            },

            # ================================================================
            # TEMPORARY & CACHE
            # ================================================================
            'temp': {
                'processing': self.base_path / "temp" / "processing",
                'cache': self.base_path / "temp" / "cache",
                'intermediate': self.base_path / "temp" / "intermediate",
            },
        }

    def ensure_all_directories(self):
        """Create ALL directories in the structure"""
        count = 0

        def create_recursive(obj, path_prefix=""):
            nonlocal count
            if isinstance(obj, dict):
                for key, value in obj.items():
                    create_recursive(value, f"{path_prefix}/{key}" if path_prefix else key)
            elif isinstance(obj, Path):
                obj.mkdir(parents=True, exist_ok=True)
                count += 1
                logger.debug(f"Created: {obj}")

        create_recursive(self.structure)
        logger.info(f"Created {count} output directories")
        return count

    def get_path(self, *path_components: str) -> Path:
        """
        Get a specific path from the structure

        Args:
            *path_components: Path components (e.g., 'procedural', 'textures', 'clouds')

        Returns:
            Path object

        Example:
            >>> structure.get_path('procedural', 'textures', 'clouds')
            PosixPath('/path/to/assets/procedural/textures/clouds')

            >>> structure.get_path('3d', 'meshes', 'fbx')
            PosixPath('/path/to/assets/3d/meshes/fbx')
        """
        current = self.structure
        path_str = " -> ".join(path_components)

        for component in path_components:
            if isinstance(current, dict):
                if component not in current:
                    raise ValueError(f"Path not found: {path_str} (failed at '{component}')")
                current = current[component]
            else:
                raise ValueError(f"Path not found: {path_str} ('{component}' is not a dictionary)")

        if not isinstance(current, Path):
            raise ValueError(f"Path incomplete: {path_str} (expected Path, got dict)")

        return current

    def list_categories(self) -> Dict[str, list]:
        """List all top-level categories and their subcategories"""
        result = {}

        for category, content in self.structure.items():
            if isinstance(content, dict):
                result[category] = list(content.keys())
            else:
                result[category] = []

        return result

    def get_all_paths(self) -> Dict[str, Path]:
        """Get flat dictionary of all endpoint paths with descriptive keys"""
        paths = {}

        def flatten(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    flatten(value, new_prefix)
            elif isinstance(obj, Path):
                paths[prefix] = obj

        flatten(self.structure)
        return paths


# ============================================================================
# GLOBAL SINGLETON
# ============================================================================

_output_structure: Optional[OutputStructure] = None


def get_output_structure(base_path: Optional[Path] = None) -> OutputStructure:
    """
    Get or create global output structure instance

    Args:
        base_path: Optional base path override

    Returns:
        Singleton OutputStructure instance
    """
    global _output_structure
    if _output_structure is None:
        _output_structure = OutputStructure(base_path)
        logger.info("Output structure initialized")
    return _output_structure


def ensure_output_directories(base_path: Optional[Path] = None) -> int:
    """
    Ensure all output directories exist

    Args:
        base_path: Optional base path override

    Returns:
        Number of directories created
    """
    structure = get_output_structure(base_path)
    return structure.ensure_all_directories()
