"""
VaultMind Forge - Game Properties & Templates
==============================================

Attach game-specific properties to Smart Objects:
- Stats (health, damage, armor, speed, etc.)
- Colors & Materials (variants, tinting, shaders)
- Buffs/Debuffs (modifiers, status effects, durations)
- Equipment Slots (attachment points, socket types)
- Loot Tables (drop chances, rarity, quantities)

Export as JSON/MD templates for:
- Different game systems (RPG, FPS, RTS, etc.)
- Character types/classes (warrior, mage, rogue)
- Factions/Guilds (unique aesthetics and stats)
- Difficulty levels (easy/normal/hard adjustments)
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict, field
import json
import yaml
from pathlib import Path


class StatType(Enum):
    """Common game stat types"""
    # Combat Stats
    HEALTH = "health"
    MAX_HEALTH = "max_health"
    ARMOR = "armor"
    DAMAGE = "damage"
    ATTACK_SPEED = "attack_speed"
    CRITICAL_CHANCE = "critical_chance"
    CRITICAL_DAMAGE = "critical_damage"

    # Movement Stats
    MOVE_SPEED = "move_speed"
    JUMP_HEIGHT = "jump_height"
    SPRINT_MULTIPLIER = "sprint_multiplier"

    # Resource Stats
    MANA = "mana"
    MAX_MANA = "max_mana"
    STAMINA = "stamina"
    MAX_STAMINA = "max_stamina"
    ENERGY = "energy"

    # Resistances
    FIRE_RESISTANCE = "fire_resistance"
    ICE_RESISTANCE = "ice_resistance"
    POISON_RESISTANCE = "poison_resistance"
    MAGIC_RESISTANCE = "magic_resistance"

    # Attributes
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    INTELLIGENCE = "intelligence"
    VITALITY = "vitality"
    LUCK = "luck"

    # Item Properties
    WEIGHT = "weight"
    VALUE = "value"
    DURABILITY = "durability"
    MAX_DURABILITY = "max_durability"
    STACK_SIZE = "stack_size"


class BuffType(Enum):
    """Buff/Debuff types"""
    STAT_MODIFIER = "stat_modifier"      # +10 strength, -20% speed
    STATUS_EFFECT = "status_effect"      # Burning, frozen, poisoned
    TEMPORARY_ABILITY = "temporary_ability"  # Double jump, invisibility
    AURA = "aura"                       # Affects nearby entities
    PASSIVE = "passive"                  # Always active


class SlotType(Enum):
    """Equipment/Attachment slot types"""
    # Character Equipment
    HEAD = "head"
    CHEST = "chest"
    LEGS = "legs"
    FEET = "feet"
    HANDS = "hands"
    BACK = "back"  # Cape/wings

    # Weapons & Tools
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    TWO_HAND = "two_hand"

    # Accessories
    RING_LEFT = "ring_left"
    RING_RIGHT = "ring_right"
    NECK = "neck"
    TRINKET = "trinket"

    # Attachment Points
    MOUNT_POINT = "mount_point"
    SOCKET = "socket"  # Gem/rune socket
    ATTACHMENT = "attachment"  # Weapon mod, scope, etc.


class RarityTier(Enum):
    """Item rarity tiers"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"


@dataclass
class ColorScheme:
    """Color/Material configuration"""
    primary_color: str = "#FFFFFF"  # Hex color
    secondary_color: str = "#808080"
    accent_color: str = "#000000"

    # Material properties
    metallic: float = 0.0  # 0.0-1.0
    roughness: float = 0.5  # 0.0-1.0
    emission: float = 0.0  # 0.0-1.0 (glow)
    opacity: float = 1.0  # 0.0-1.0 (transparency)

    # Shader/Effect
    shader_type: str = "standard"  # standard, cel-shaded, hologram, etc.
    special_effects: List[str] = field(default_factory=list)  # ["glow", "particles", "aura"]


@dataclass
class Buff:
    """Buff/Debuff definition"""
    name: str
    buff_type: BuffType
    stat_modifiers: Dict[str, Union[int, float]] = field(default_factory=dict)
    duration: Optional[float] = None  # Seconds (None = permanent)
    stack_count: int = 1
    max_stacks: int = 1
    description: str = ""


@dataclass
class EquipmentSlot:
    """Equipment or attachment slot"""
    slot_type: SlotType
    position: tuple = (0.0, 0.0, 0.0)  # Local offset
    rotation: tuple = (0.0, 0.0, 0.0)  # Local rotation
    scale: tuple = (1.0, 1.0, 1.0)  # Scale modifier
    allowed_types: List[str] = field(default_factory=list)  # ["sword", "axe", "staff"]
    required: bool = False  # Must have item in slot


@dataclass
class LootEntry:
    """Loot table entry"""
    item_id: str
    drop_chance: float  # 0.0-1.0
    quantity_min: int = 1
    quantity_max: int = 1
    rarity: RarityTier = RarityTier.COMMON
    conditions: Dict[str, Any] = field(default_factory=dict)  # {"player_level_min": 10}


class GameProperties:
    """
    Game-specific properties for Smart Objects.

    Attaches stats, colors, buffs, slots, and loot to any object.
    """

    def __init__(self, name: str, object_id: Optional[str] = None):
        self.name = name
        self.object_id = object_id or name.lower().replace(" ", "_")

        # Stats
        self.stats: Dict[StatType, Union[int, float]] = {}

        # Colors & Materials
        self.color_schemes: Dict[str, ColorScheme] = {
            "default": ColorScheme()
        }
        self.active_scheme = "default"

        # Buffs/Debuffs
        self.buffs: List[Buff] = []

        # Equipment Slots
        self.slots: List[EquipmentSlot] = []

        # Loot Table
        self.loot_table: List[LootEntry] = []

        # Item Classification
        self.rarity = RarityTier.COMMON
        self.category = "misc"  # weapon, armor, consumable, quest, etc.
        self.sub_category = ""  # sword, potion, key, etc.

        # Flags
        self.tradeable = True
        self.droppable = True
        self.sellable = True
        self.stackable = False
        self.quest_item = False
        self.soulbound = False  # Binds to player

        # Gameplay
        self.level_requirement = 1
        self.class_requirement = []  # ["warrior", "paladin"]
        self.faction_requirement = None

        # Tags for filtering
        self.gameplay_tags = set()

    # ========== Stats ==========

    def set_stat(self, stat: Union[StatType, str], value: Union[int, float]) -> 'GameProperties':
        """Set a stat value"""
        if isinstance(stat, str):
            stat = StatType(stat)
        self.stats[stat] = value
        return self

    def get_stat(self, stat: Union[StatType, str]) -> Union[int, float]:
        """Get a stat value (returns 0 if not set)"""
        if isinstance(stat, str):
            stat = StatType(stat)
        return self.stats.get(stat, 0)

    def modify_stat(self, stat: Union[StatType, str], amount: Union[int, float]) -> 'GameProperties':
        """Modify a stat by amount (additive)"""
        if isinstance(stat, str):
            stat = StatType(stat)
        current = self.get_stat(stat)
        self.stats[stat] = current + amount
        return self

    def calculate_total_stats(self) -> Dict[str, Union[int, float]]:
        """Calculate total stats including buffs"""
        total = {stat.value: value for stat, value in self.stats.items()}

        # Apply buff modifiers
        for buff in self.buffs:
            for stat_name, modifier in buff.stat_modifiers.items():
                if isinstance(modifier, str) and '%' in modifier:
                    # Percentage modifier
                    percent = float(modifier.rstrip('%')) / 100.0
                    current = total.get(stat_name, 0)
                    total[stat_name] = current * (1.0 + percent)
                else:
                    # Flat modifier
                    total[stat_name] = total.get(stat_name, 0) + modifier

        return total

    # ========== Colors & Materials ==========

    def add_color_scheme(self, name: str, scheme: ColorScheme) -> 'GameProperties':
        """Add a color scheme variant"""
        self.color_schemes[name] = scheme
        return self

    def set_active_scheme(self, name: str) -> 'GameProperties':
        """Set active color scheme"""
        if name in self.color_schemes:
            self.active_scheme = name
        return self

    def get_active_colors(self) -> ColorScheme:
        """Get currently active color scheme"""
        return self.color_schemes[self.active_scheme]

    # ========== Buffs ==========

    def add_buff(self, buff: Buff) -> 'GameProperties':
        """Add a buff/debuff"""
        self.buffs.append(buff)
        return self

    def remove_buff(self, name: str) -> 'GameProperties':
        """Remove buff by name"""
        self.buffs = [b for b in self.buffs if b.name != name]
        return self

    # ========== Equipment Slots ==========

    def add_slot(self, slot: EquipmentSlot) -> 'GameProperties':
        """Add an equipment/attachment slot"""
        self.slots.append(slot)
        return self

    def get_slots_by_type(self, slot_type: SlotType) -> List[EquipmentSlot]:
        """Get all slots of a specific type"""
        return [s for s in self.slots if s.slot_type == slot_type]

    # ========== Loot ==========

    def add_loot(self, entry: LootEntry) -> 'GameProperties':
        """Add a loot table entry"""
        self.loot_table.append(entry)
        return self

    def generate_loot(self, luck_modifier: float = 1.0) -> List[Dict[str, Any]]:
        """Generate loot drops based on chances"""
        import random
        drops = []
        for entry in self.loot_table:
            chance = entry.drop_chance * luck_modifier
            if random.random() < chance:
                quantity = random.randint(entry.quantity_min, entry.quantity_max)
                drops.append({
                    "item_id": entry.item_id,
                    "quantity": quantity,
                    "rarity": entry.rarity.value
                })
        return drops

    # ========== Export ==========

    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary"""
        return {
            "object_id": self.object_id,
            "name": self.name,
            "rarity": self.rarity.value,
            "category": self.category,
            "sub_category": self.sub_category,

            "stats": {stat.value: value for stat, value in self.stats.items()},

            "color_schemes": {
                name: asdict(scheme) for name, scheme in self.color_schemes.items()
            },
            "active_scheme": self.active_scheme,

            "buffs": [
                {**asdict(buff), "buff_type": buff.buff_type.value}
                for buff in self.buffs
            ],

            "slots": [
                {**asdict(slot), "slot_type": slot.slot_type.value}
                for slot in self.slots
            ],

            "loot_table": [
                {**asdict(entry), "rarity": entry.rarity.value}
                for entry in self.loot_table
            ],

            "flags": {
                "tradeable": self.tradeable,
                "droppable": self.droppable,
                "sellable": self.sellable,
                "stackable": self.stackable,
                "quest_item": self.quest_item,
                "soulbound": self.soulbound,
            },

            "requirements": {
                "level": self.level_requirement,
                "classes": self.class_requirement,
                "faction": self.faction_requirement,
            },

            "tags": list(self.gameplay_tags),
        }

    def to_json(self, path: str, pretty: bool = True):
        """Export to JSON file"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2 if pretty else None)

    def to_yaml(self, path: str):
        """Export to YAML file"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)

    def to_markdown(self, path: str):
        """Export to Markdown (human-readable documentation)"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        md = []
        md.append(f"# {self.name}\n")
        md.append(f"**ID:** `{self.object_id}`  ")
        md.append(f"**Rarity:** {self.rarity.value.title()}  ")
        md.append(f"**Category:** {self.category} / {self.sub_category}\n")

        # Stats
        if self.stats:
            md.append("## Base Stats\n")
            md.append("| Stat | Value |")
            md.append("|------|-------|")
            for stat, value in self.stats.items():
                md.append(f"| {stat.value.replace('_', ' ').title()} | {value} |")
            md.append("")

        # Buffs
        if self.buffs:
            md.append("## Buffs/Effects\n")
            for buff in self.buffs:
                md.append(f"### {buff.name}")
                md.append(f"- **Type:** {buff.buff_type.value}")
                if buff.duration:
                    md.append(f"- **Duration:** {buff.duration}s")
                if buff.stat_modifiers:
                    md.append(f"- **Modifiers:**")
                    for stat, mod in buff.stat_modifiers.items():
                        md.append(f"  - {stat}: {mod}")
                if buff.description:
                    md.append(f"- **Description:** {buff.description}")
                md.append("")

        # Color Schemes
        if len(self.color_schemes) > 1:
            md.append("## Color Variants\n")
            for name, scheme in self.color_schemes.items():
                active = " (Active)" if name == self.active_scheme else ""
                md.append(f"### {name.title()}{active}")
                md.append(f"- Primary: `{scheme.primary_color}`")
                md.append(f"- Secondary: `{scheme.secondary_color}`")
                md.append(f"- Accent: `{scheme.accent_color}`")
                md.append(f"- Material: Metallic={scheme.metallic}, Roughness={scheme.roughness}")
                md.append("")

        # Equipment Slots
        if self.slots:
            md.append("## Equipment Slots\n")
            md.append("| Slot Type | Position | Allowed Types |")
            md.append("|-----------|----------|---------------|")
            for slot in self.slots:
                allowed = ", ".join(slot.allowed_types) if slot.allowed_types else "Any"
                md.append(f"| {slot.slot_type.value} | {slot.position} | {allowed} |")
            md.append("")

        # Loot Table
        if self.loot_table:
            md.append("## Loot Table\n")
            md.append("| Item | Drop Chance | Quantity | Rarity |")
            md.append("|------|-------------|----------|--------|")
            for entry in self.loot_table:
                qty = f"{entry.quantity_min}-{entry.quantity_max}" if entry.quantity_min != entry.quantity_max else str(entry.quantity_min)
                md.append(f"| {entry.item_id} | {entry.drop_chance*100:.1f}% | {qty} | {entry.rarity.value} |")
            md.append("")

        # Requirements
        md.append("## Requirements\n")
        md.append(f"- **Level:** {self.level_requirement}")
        if self.class_requirement:
            md.append(f"- **Classes:** {', '.join(self.class_requirement)}")
        if self.faction_requirement:
            md.append(f"- **Faction:** {self.faction_requirement}")
        md.append("")

        # Flags
        md.append("## Flags\n")
        flags = []
        if self.tradeable:
            flags.append("Tradeable")
        if self.droppable:
            flags.append("Droppable")
        if self.sellable:
            flags.append("Sellable")
        if self.stackable:
            flags.append("Stackable")
        if self.quest_item:
            flags.append("Quest Item")
        if self.soulbound:
            flags.append("Soulbound")
        md.append(", ".join(flags))

        with open(path, 'w') as f:
            f.write('\n'.join(md))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameProperties':
        """Import from dictionary"""
        props = cls(name=data["name"], object_id=data.get("object_id"))

        # Load stats
        for stat_name, value in data.get("stats", {}).items():
            props.set_stat(stat_name, value)

        # Load color schemes
        props.color_schemes.clear()
        for name, scheme_data in data.get("color_schemes", {}).items():
            props.color_schemes[name] = ColorScheme(**scheme_data)
        props.active_scheme = data.get("active_scheme", "default")

        # Load buffs
        for buff_data in data.get("buffs", []):
            buff_data["buff_type"] = BuffType(buff_data["buff_type"])
            props.buffs.append(Buff(**buff_data))

        # Load slots
        for slot_data in data.get("slots", []):
            slot_data["slot_type"] = SlotType(slot_data["slot_type"])
            props.slots.append(EquipmentSlot(**slot_data))

        # Load loot table
        for loot_data in data.get("loot_table", []):
            loot_data["rarity"] = RarityTier(loot_data["rarity"])
            props.loot_table.append(LootEntry(**loot_data))

        # Load metadata
        props.rarity = RarityTier(data.get("rarity", "common"))
        props.category = data.get("category", "misc")
        props.sub_category = data.get("sub_category", "")

        # Load flags
        flags = data.get("flags", {})
        props.tradeable = flags.get("tradeable", True)
        props.droppable = flags.get("droppable", True)
        props.sellable = flags.get("sellable", True)
        props.stackable = flags.get("stackable", False)
        props.quest_item = flags.get("quest_item", False)
        props.soulbound = flags.get("soulbound", False)

        # Load requirements
        req = data.get("requirements", {})
        props.level_requirement = req.get("level", 1)
        props.class_requirement = req.get("classes", [])
        props.faction_requirement = req.get("faction")

        # Load tags
        props.gameplay_tags = set(data.get("tags", []))

        return props

    @classmethod
    def from_json(cls, path: str) -> 'GameProperties':
        """Import from JSON file"""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_yaml(cls, path: str) -> 'GameProperties':
        """Import from YAML file"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
