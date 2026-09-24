"""
VaultMind Forge - Smart Object System
======================================

Smart objects are geometry with semantic meaning, behavior, and context.
Every object knows what it is, what it does, and how to configure itself.

A Box isn't just a cube - it could be:
- Static mesh (decorative pillar)
- Actor (physics-enabled crate)
- Collision hull (invisible boundary)
- Marker (editor gizmo, not rendered)
- Interactive (button, lever, door)
- Component (part of larger assembly)

The system auto-configures based on naming, type, and context.
"""

from typing import Optional, Dict, List, Any, Union, Tuple
from enum import Enum
from datetime import datetime
from pathlib import Path
import json
import yaml

from .mesh import Mesh
from .primitives_all import PrimitiveBase


class ObjectType(Enum):
    """Semantic object types with different behaviors"""
    STATIC_MESH = "static_mesh"           # Decorative, non-moving (pillars, walls)
    ACTOR = "actor"                       # Dynamic, can move/animate (crates, props)
    COLLISION = "collision"               # Invisible, physics only (character hulls)
    MARKER = "marker"                     # Editor-only, gizmos, spawn points
    INTERACTIVE = "interactive"           # Player can interact (buttons, levers)
    TRIGGER = "trigger"                   # Invisible volume, event-based (doorways)
    COMPONENT = "component"               # Part of larger assembly
    LIGHT_VOLUME = "light_volume"         # Lighting geometry (soft boxes, reflectors)
    CAMERA_RIG = "camera_rig"             # Camera track/dolly geometry
    NAVMESH_BLOCKER = "navmesh_blocker"   # AI pathfinding obstacle
    DESTRUCTIBLE = "destructible"         # Can be broken/destroyed
    VEHICLE = "vehicle"                   # Driveable/rideable
    WEAPON = "weapon"                     # Equippable weapon
    PICKUP = "pickup"                     # Collectible item


class PhysicsType(Enum):
    """Physics behavior modes"""
    NONE = "none"                   # No physics
    STATIC = "static"               # Immovable, other objects collide with it
    DYNAMIC = "dynamic"             # Fully simulated physics
    KINEMATIC = "kinematic"         # Movable but not physics-simulated
    TRIGGER = "trigger"             # No collision, only triggers events


class RenderMode(Enum):
    """How the object should be rendered"""
    OPAQUE = "opaque"               # Normal solid rendering
    TRANSPARENT = "transparent"     # Alpha blending
    MASKED = "masked"               # Alpha cutout
    WIREFRAME = "wireframe"         # Debug wireframe
    INVISIBLE = "invisible"         # Not rendered (collision/trigger only)
    EDITOR_ONLY = "editor_only"     # Only visible in editor


class InteractionType(Enum):
    """Types of player interaction"""
    NONE = "none"
    CLICK = "click"                 # Mouse click / tap
    HOLD = "hold"                   # Press and hold
    PROXIMITY = "proximity"         # Auto-trigger when player nearby
    COLLISION = "collision"         # Trigger on physical contact
    RAYCAST = "raycast"            # Look at / aim at
    CUSTOM = "custom"               # Custom scripted interaction


class SmartObject:
    """
    Intelligent asset object with geometry, semantics, and behavior.

    Auto-configures based on context and provides rich metadata for export.
    """

    def __init__(self,
                 primitive: PrimitiveBase,
                 name: str,
                 object_type: Optional[ObjectType] = None,
                 auto_configure: bool = True):
        """
        Create a smart object from a primitive.

        Args:
            primitive: The geometric primitive
            name: Object name (used for auto-configuration)
            object_type: Explicit object type (if None, auto-detect from name)
            auto_configure: Auto-configure properties based on type/name
        """
        self.primitive = primitive
        self.name = name
        self.mesh = None  # Built lazily

        # Auto-detect object type from name if not specified
        if object_type is None and auto_configure:
            self.object_type = self._infer_object_type(name)
        else:
            self.object_type = object_type or ObjectType.STATIC_MESH

        # Core properties (auto-configured based on type)
        self.physics_type = PhysicsType.NONE
        self.render_mode = RenderMode.OPAQUE
        self.interaction_type = InteractionType.NONE

        # Physics properties
        self.mass = 1.0
        self.friction = 0.5
        self.restitution = 0.3  # Bounciness
        self.linear_damping = 0.1
        self.angular_damping = 0.1

        # Transform
        self.position = (0.0, 0.0, 0.0)
        self.rotation = (0.0, 0.0, 0.0)  # Euler angles
        self.scale = (1.0, 1.0, 1.0)

        # Interaction
        self.interaction_points = []  # List of (x, y, z) positions
        self.interaction_radius = 1.0
        self.interaction_prompt = ""  # "Press E to open"

        # Animation/Movement
        self.animation_data = {}  # Keyframes, curves, etc.
        self.movement_pattern = None  # "patrol", "rotate", "bounce", etc.
        self.movement_params = {}

        # Grouping/Hierarchy
        self.parent = None
        self.children = []
        self.group_id = None
        self.assembly_role = None  # "base", "door", "handle", etc.

        # Tags for filtering/searching
        self.tags = set()

        # Custom properties (user-defined key-value pairs)
        self.custom_properties = {}

        # Metadata
        self.created_at = datetime.now().isoformat()
        self.modified_at = self.created_at
        self.version = 1
        self.author = "VaultMind Forge"

        # Auto-configure if enabled
        if auto_configure:
            self._auto_configure()

    def _infer_object_type(self, name: str) -> ObjectType:
        """Intelligently infer object type from name"""
        name_lower = name.lower()

        # Collision detection
        if any(keyword in name_lower for keyword in ["hull", "collision", "collider", "hitbox"]):
            return ObjectType.COLLISION

        # Marker/Gizmo detection
        if any(keyword in name_lower for keyword in ["marker", "spawn", "point", "gizmo"]):
            return ObjectType.MARKER

        # Trigger detection
        if any(keyword in name_lower for keyword in ["trigger", "zone", "volume"]):
            return ObjectType.TRIGGER

        # Interactive detection
        if any(keyword in name_lower for keyword in ["button", "lever", "switch", "door", "chest"]):
            return ObjectType.INTERACTIVE

        # Destructible detection
        if any(keyword in name_lower for keyword in ["crate", "barrel", "vase", "pot", "breakable"]):
            return ObjectType.DESTRUCTIBLE

        # Pickup detection
        if any(keyword in name_lower for keyword in ["coin", "gem", "potion", "pickup", "collectible"]):
            return ObjectType.PICKUP

        # Weapon detection
        if any(keyword in name_lower for keyword in ["sword", "gun", "axe", "weapon", "blade"]):
            return ObjectType.WEAPON

        # Light volume detection
        if any(keyword in name_lower for keyword in ["light", "softbox", "reflector", "lamp"]):
            return ObjectType.LIGHT_VOLUME

        # Camera rig detection
        if any(keyword in name_lower for keyword in ["camera", "dolly", "track", "rig"]):
            return ObjectType.CAMERA_RIG

        # NavMesh detection
        if any(keyword in name_lower for keyword in ["navmesh", "blocker", "nav_block"]):
            return ObjectType.NAVMESH_BLOCKER

        # Component detection
        if any(keyword in name_lower for keyword in ["component", "part", "piece"]):
            return ObjectType.COMPONENT

        # Static mesh detection (pillars, walls, floors - architectural)
        if any(keyword in name_lower for keyword in ["pillar", "column", "wall", "floor", "ceiling", "beam"]):
            return ObjectType.STATIC_MESH

        # Default to Actor for physics-enabled props
        return ObjectType.ACTOR

    def _auto_configure(self):
        """Auto-configure properties based on object type"""

        if self.object_type == ObjectType.STATIC_MESH:
            self.physics_type = PhysicsType.STATIC
            self.render_mode = RenderMode.OPAQUE
            self.tags.add("static")
            self.tags.add("environment")

        elif self.object_type == ObjectType.ACTOR:
            self.physics_type = PhysicsType.DYNAMIC
            self.render_mode = RenderMode.OPAQUE
            self.mass = 10.0
            self.tags.add("dynamic")
            self.tags.add("prop")

        elif self.object_type == ObjectType.COLLISION:
            self.physics_type = PhysicsType.STATIC
            self.render_mode = RenderMode.INVISIBLE
            self.tags.add("collision")
            self.tags.add("invisible")

        elif self.object_type == ObjectType.MARKER:
            self.physics_type = PhysicsType.NONE
            self.render_mode = RenderMode.EDITOR_ONLY
            self.tags.add("marker")
            self.tags.add("editor_only")

        elif self.object_type == ObjectType.INTERACTIVE:
            self.physics_type = PhysicsType.STATIC
            self.render_mode = RenderMode.OPAQUE
            self.interaction_type = InteractionType.CLICK
            self.interaction_prompt = f"Press E to use {self.name}"
            self.tags.add("interactive")

        elif self.object_type == ObjectType.TRIGGER:
            self.physics_type = PhysicsType.TRIGGER
            self.render_mode = RenderMode.INVISIBLE
            self.interaction_type = InteractionType.COLLISION
            self.tags.add("trigger")
            self.tags.add("invisible")

        elif self.object_type == ObjectType.DESTRUCTIBLE:
            self.physics_type = PhysicsType.DYNAMIC
            self.render_mode = RenderMode.OPAQUE
            self.mass = 15.0
            self.custom_properties["health"] = 100
            self.custom_properties["break_force"] = 50.0
            self.tags.add("destructible")
            self.tags.add("breakable")

        elif self.object_type == ObjectType.PICKUP:
            self.physics_type = PhysicsType.KINEMATIC
            self.render_mode = RenderMode.OPAQUE
            self.interaction_type = InteractionType.PROXIMITY
            self.interaction_radius = 1.5
            self.movement_pattern = "rotate"
            self.movement_params = {"axis": "y", "speed": 45.0}  # Rotate 45 deg/sec
            self.tags.add("pickup")
            self.tags.add("collectible")

        elif self.object_type == ObjectType.LIGHT_VOLUME:
            self.physics_type = PhysicsType.NONE
            self.render_mode = RenderMode.INVISIBLE
            self.tags.add("lighting")
            self.tags.add("invisible")

        elif self.object_type == ObjectType.CAMERA_RIG:
            self.physics_type = PhysicsType.KINEMATIC
            self.render_mode = RenderMode.EDITOR_ONLY
            self.tags.add("camera")
            self.tags.add("cinematic")

        elif self.object_type == ObjectType.NAVMESH_BLOCKER:
            self.physics_type = PhysicsType.NONE
            self.render_mode = RenderMode.INVISIBLE
            self.tags.add("navmesh")
            self.tags.add("ai")

        elif self.object_type == ObjectType.WEAPON:
            self.physics_type = PhysicsType.KINEMATIC
            self.render_mode = RenderMode.OPAQUE
            self.custom_properties["damage"] = 25
            self.custom_properties["attack_speed"] = 1.0
            self.tags.add("weapon")
            self.tags.add("equippable")

        elif self.object_type == ObjectType.COMPONENT:
            self.physics_type = PhysicsType.NONE
            self.render_mode = RenderMode.OPAQUE
            self.tags.add("component")

    def build(self) -> 'SmartObject':
        """Build the mesh if not already built"""
        if self.mesh is None:
            self.mesh = self.primitive.build()
        return self

    def add_tag(self, *tags: str) -> 'SmartObject':
        """Add tags for filtering/searching"""
        self.tags.update(tags)
        return self

    def set_physics(self, physics_type: PhysicsType,
                   mass: float = None,
                   friction: float = None,
                   restitution: float = None) -> 'SmartObject':
        """Configure physics properties"""
        self.physics_type = physics_type
        if mass is not None:
            self.mass = mass
        if friction is not None:
            self.friction = friction
        if restitution is not None:
            self.restitution = restitution
        return self

    def set_transform(self,
                     position: Tuple[float, float, float] = None,
                     rotation: Tuple[float, float, float] = None,
                     scale: Tuple[float, float, float] = None) -> 'SmartObject':
        """Set transform properties"""
        if position is not None:
            self.position = position
        if rotation is not None:
            self.rotation = rotation
        if scale is not None:
            self.scale = scale
        return self

    def add_interaction_point(self, position: Tuple[float, float, float],
                             prompt: str = None) -> 'SmartObject':
        """Add an interaction point"""
        self.interaction_points.append(position)
        if prompt:
            self.interaction_prompt = prompt
        return self

    def set_movement(self, pattern: str, **params) -> 'SmartObject':
        """Configure movement/animation pattern"""
        self.movement_pattern = pattern
        self.movement_params = params
        return self

    def set_parent(self, parent: 'SmartObject') -> 'SmartObject':
        """Set parent in hierarchy"""
        self.parent = parent
        if self not in parent.children:
            parent.children.append(self)
        return self

    def add_child(self, child: 'SmartObject') -> 'SmartObject':
        """Add child to hierarchy"""
        child.set_parent(self)
        return self

    def set_property(self, key: str, value: Any) -> 'SmartObject':
        """Set custom property"""
        self.custom_properties[key] = value
        self.modified_at = datetime.now().isoformat()
        return self

    def to_schema(self) -> Dict[str, Any]:
        """
        Export complete object schema with all properties.
        This preserves EVERYTHING - geometry, behavior, state, hierarchy.
        """
        self.build()  # Ensure mesh is built

        schema = {
            "schema_version": "1.0.0",
            "object": {
                "name": self.name,
                "type": self.object_type.value,
                "version": self.version,
                "created_at": self.created_at,
                "modified_at": self.modified_at,
                "author": self.author,
            },

            "primitive": {
                "type": self.primitive.__class__.__name__,
                "parameters": self.primitive._metadata.get("parameters", {}),
                "detail_level": self.primitive._metadata.get("detail_level"),
            },

            "geometry": {
                "vertex_count": self.mesh.vertex_count(),
                "triangle_count": self.mesh.triangle_count(),
                "bounds": {
                    "min": self.mesh.bounds_min(),
                    "max": self.mesh.bounds_max(),
                },
            },

            "physics": {
                "type": self.physics_type.value,
                "mass": self.mass,
                "friction": self.friction,
                "restitution": self.restitution,
                "linear_damping": self.linear_damping,
                "angular_damping": self.angular_damping,
            },

            "rendering": {
                "mode": self.render_mode.value,
            },

            "transform": {
                "position": self.position,
                "rotation": self.rotation,
                "scale": self.scale,
            },

            "interaction": {
                "type": self.interaction_type.value,
                "radius": self.interaction_radius,
                "prompt": self.interaction_prompt,
                "points": self.interaction_points,
            },

            "animation": {
                "movement_pattern": self.movement_pattern,
                "movement_params": self.movement_params,
                "animation_data": self.animation_data,
            },

            "hierarchy": {
                "parent": self.parent.name if self.parent else None,
                "children": [child.name for child in self.children],
                "group_id": self.group_id,
                "assembly_role": self.assembly_role,
            },

            "metadata": {
                "tags": list(self.tags),
                "custom_properties": self.custom_properties,
            },
        }

        return schema

    def save_json(self, path: str, include_mesh: bool = True):
        """Save complete schema to JSON"""
        schema = self.to_schema()

        Path(path).parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(schema, f, indent=2)

        # Also save mesh geometry if requested
        if include_mesh:
            mesh_path = str(Path(path).with_suffix('.obj'))
            self.mesh.save_obj(mesh_path)

    def save_yaml(self, path: str, include_mesh: bool = True):
        """Save complete schema to YAML"""
        schema = self.to_schema()

        Path(path).parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            yaml.dump(schema, f, default_flow_style=False, sort_keys=False)

        # Also save mesh geometry if requested
        if include_mesh:
            mesh_path = str(Path(path).with_suffix('.obj'))
            self.mesh.save_obj(mesh_path)

    @classmethod
    def from_schema(cls, schema: Dict[str, Any], primitive: PrimitiveBase) -> 'SmartObject':
        """Recreate object from schema (round-trip support)"""
        obj = cls(
            primitive=primitive,
            name=schema["object"]["name"],
            object_type=ObjectType(schema["object"]["type"]),
            auto_configure=False  # Don't auto-configure, use schema values
        )

        # Restore all properties from schema
        obj.version = schema["object"]["version"]
        obj.created_at = schema["object"]["created_at"]
        obj.modified_at = schema["object"]["modified_at"]
        obj.author = schema["object"]["author"]

        # Physics
        physics = schema["physics"]
        obj.physics_type = PhysicsType(physics["type"])
        obj.mass = physics["mass"]
        obj.friction = physics["friction"]
        obj.restitution = physics["restitution"]
        obj.linear_damping = physics["linear_damping"]
        obj.angular_damping = physics["angular_damping"]

        # Rendering
        obj.render_mode = RenderMode(schema["rendering"]["mode"])

        # Transform
        transform = schema["transform"]
        obj.position = tuple(transform["position"])
        obj.rotation = tuple(transform["rotation"])
        obj.scale = tuple(transform["scale"])

        # Interaction
        interaction = schema["interaction"]
        obj.interaction_type = InteractionType(interaction["type"])
        obj.interaction_radius = interaction["radius"]
        obj.interaction_prompt = interaction["prompt"]
        obj.interaction_points = [tuple(p) for p in interaction["points"]]

        # Animation
        animation = schema["animation"]
        obj.movement_pattern = animation["movement_pattern"]
        obj.movement_params = animation["movement_params"]
        obj.animation_data = animation["animation_data"]

        # Hierarchy (parent/children restored separately after all objects loaded)
        hierarchy = schema["hierarchy"]
        obj.group_id = hierarchy["group_id"]
        obj.assembly_role = hierarchy["assembly_role"]

        # Metadata
        metadata = schema["metadata"]
        obj.tags = set(metadata["tags"])
        obj.custom_properties = metadata["custom_properties"]

        return obj

    def export_for_engine(self, engine: str, output_dir: str):
        """
        Export object with engine-specific configuration.
        Creates both geometry and metadata files.
        """
        self.build()

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Export geometry
        mesh_file = output_path / f"{self.name}.obj"

        if engine == "unity":
            self.mesh.to_unity(str(mesh_file))
        elif engine == "unreal":
            self.mesh.to_unreal(str(mesh_file))
        elif engine == "godot":
            self.mesh.to_godot(str(mesh_file))
        elif engine == "lumix":
            self.mesh.to_lumix(str(mesh_file))
        elif engine == "cryengine":
            self.mesh.to_cryengine(str(mesh_file))
        else:
            self.mesh.save_obj(str(mesh_file))

        # Export metadata schema
        meta_file = output_path / f"{self.name}_meta.json"
        self.save_json(str(meta_file), include_mesh=False)

        return str(mesh_file), str(meta_file)

    def __repr__(self):
        return (f"SmartObject(name='{self.name}', type={self.object_type.value}, "
                f"physics={self.physics_type.value}, render={self.render_mode.value})")


class Assembly:
    """
    Group of SmartObjects that work together as a single unit.
    Example: Door assembly with frame, door panel, hinges, handle.
    """

    def __init__(self, name: str):
        self.name = name
        self.objects = []
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "assembly_type": None,
        }

    def add_object(self, obj: SmartObject, role: str = None) -> 'Assembly':
        """Add object to assembly with optional role"""
        obj.group_id = self.name
        if role:
            obj.assembly_role = role
        self.objects.append(obj)
        return self

    def export_all(self, engine: str, output_dir: str):
        """Export entire assembly"""
        assembly_dir = Path(output_dir) / self.name
        assembly_dir.mkdir(parents=True, exist_ok=True)

        exported_files = []
        for obj in self.objects:
            mesh_file, meta_file = obj.export_for_engine(engine, str(assembly_dir))
            exported_files.append((mesh_file, meta_file))

        # Create assembly manifest
        manifest = {
            "assembly_name": self.name,
            "object_count": len(self.objects),
            "objects": [
                {
                    "name": obj.name,
                    "role": obj.assembly_role,
                    "type": obj.object_type.value,
                }
                for obj in self.objects
            ],
            "metadata": self.metadata,
        }

        manifest_file = assembly_dir / "assembly_manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

        return exported_files, str(manifest_file)
