//! Size Templates for Game Engines and CAD Standards
//!
//! Based on research of actual game engines:
//! - Unity: 1 unit = 1 meter
//! - Unreal: 1 unit = 1 centimeter (UU = Unreal Unit)
//! - CryEngine: 1 unit = 1 centimeter
//! - Source Engine: 1 unit = 0.75 inches (16 units = 1 foot)
//! - Godot: 1 unit = 1 meter
//! - Lumix: 1 unit = 1 meter
//!
//! Common game object sizes (in meters):
//! - Human: 1.8m tall
//! - Door: 2.0m x 1.0m
//! - Wall thickness: 0.15m - 0.30m
//! - Ceiling height: 2.4m - 3.0m
//! - Stairs: 0.18m rise, 0.28m run

use nalgebra::Vector3;

/// Standard measurement units
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Unit {
    Meters,
    Centimeters,
    Feet,
    Inches,
}

impl Unit {
    /// Convert to meters (base unit)
    pub fn to_meters(&self, value: f32) -> f32 {
        match self {
            Unit::Meters => value,
            Unit::Centimeters => value / 100.0,
            Unit::Feet => value * 0.3048,
            Unit::Inches => value * 0.0254,
        }
    }

    /// Convert from meters
    pub fn from_meters(&self, meters: f32) -> f32 {
        match self {
            Unit::Meters => meters,
            Unit::Centimeters => meters * 100.0,
            Unit::Feet => meters / 0.3048,
            Unit::Inches => meters / 0.0254,
        }
    }
}

/// Size template categories
#[derive(Debug, Clone, Copy)]
pub enum TemplateCategory {
    Character,
    Architecture,
    Furniture,
    Vehicle,
    Prop,
    Environment,
}

/// Predefined size templates
#[derive(Debug, Clone)]
pub struct SizeTemplate {
    pub name: &'static str,
    pub category: TemplateCategory,
    pub size: Vector3<f32>, // In meters
    pub description: &'static str,
}

impl SizeTemplate {
    /// Get size for specific engine (with unit conversion)
    pub fn for_unity(&self) -> Vector3<f32> {
        self.size // Unity uses meters
    }

    pub fn for_unreal(&self) -> Vector3<f32> {
        self.size * 100.0 // Unreal uses cm
    }

    pub fn for_cryengine(&self) -> Vector3<f32> {
        self.size * 100.0 // CryEngine uses cm
    }

    pub fn for_source(&self) -> Vector3<f32> {
        self.size * 52.5 // Source: 16 units = 1 foot
    }

    pub fn for_lumix(&self) -> Vector3<f32> {
        self.size // Lumix uses meters
    }

    pub fn for_godot(&self) -> Vector3<f32> {
        self.size // Godot uses meters
    }
}

/// Standard character sizes
pub mod character {
    use super::*;

    pub const HUMAN_MALE: SizeTemplate = SizeTemplate {
        name: "Human Male",
        category: TemplateCategory::Character,
        size: Vector3::new(0.5, 1.80, 0.3),
        description: "Average adult male: 1.80m tall",
    };

    pub const HUMAN_FEMALE: SizeTemplate = SizeTemplate {
        name: "Human Female",
        category: TemplateCategory::Character,
        size: Vector3::new(0.45, 1.65, 0.28),
        description: "Average adult female: 1.65m tall",
    };

    pub const CHILD: SizeTemplate = SizeTemplate {
        name: "Child",
        category: TemplateCategory::Character,
        size: Vector3::new(0.35, 1.20, 0.22),
        description: "Child (8-10 years): 1.20m tall",
    };

    pub const CAPSULE_COLLISION: SizeTemplate = SizeTemplate {
        name: "Character Capsule",
        category: TemplateCategory::Character,
        size: Vector3::new(0.4, 1.8, 0.4),
        description: "Standard character controller capsule",
    };
}

/// Architecture templates (real-world standards)
pub mod architecture {
    use super::*;

    pub const DOOR_STANDARD: SizeTemplate = SizeTemplate {
        name: "Standard Door",
        category: TemplateCategory::Architecture,
        size: Vector3::new(0.9, 2.0, 0.05),
        description: "Residential door: 2.0m x 0.9m",
    };

    pub const DOOR_DOUBLE: SizeTemplate = SizeTemplate {
        name: "Double Door",
        category: TemplateCategory::Architecture,
        size: Vector3::new(1.8, 2.0, 0.05),
        description: "Double door: 2.0m x 1.8m total",
    };

    pub const WALL_INTERIOR: SizeTemplate = SizeTemplate {
        name: "Interior Wall",
        category: TemplateCategory::Architecture,
        size: Vector3::new(4.0, 2.4, 0.15),
        description: "Interior wall: 15cm thick, 2.4m high",
    };

    pub const WALL_EXTERIOR: SizeTemplate = SizeTemplate {
        name: "Exterior Wall",
        category: TemplateCategory::Architecture,
        size: Vector3::new(4.0, 2.4, 0.30),
        description: "Exterior wall: 30cm thick, 2.4m high",
    };

    pub const WINDOW_STANDARD: SizeTemplate = SizeTemplate {
        name: "Standard Window",
        category: TemplateCategory::Architecture,
        size: Vector3::new(1.2, 1.5, 0.1),
        description: "Standard window: 1.2m x 1.5m",
    };

    pub const STAIRS_STEP: SizeTemplate = SizeTemplate {
        name: "Stair Step",
        category: TemplateCategory::Architecture,
        size: Vector3::new(1.0, 0.18, 0.28),
        description: "Standard stair: 18cm rise, 28cm run",
    };

    pub const CEILING_RESIDENTIAL: SizeTemplate = SizeTemplate {
        name: "Residential Ceiling",
        category: TemplateCategory::Architecture,
        size: Vector3::new(4.0, 2.4, 0.02),
        description: "Standard ceiling height: 2.4m",
    };

    pub const CEILING_COMMERCIAL: SizeTemplate = SizeTemplate {
        name: "Commercial Ceiling",
        category: TemplateCategory::Architecture,
        size: Vector3::new(6.0, 3.0, 0.02),
        description: "Commercial ceiling height: 3.0m",
    };
}

/// Furniture templates
pub mod furniture {
    use super::*;

    pub const TABLE_DINING: SizeTemplate = SizeTemplate {
        name: "Dining Table",
        category: TemplateCategory::Furniture,
        size: Vector3::new(1.8, 0.75, 0.9),
        description: "6-person dining table",
    };

    pub const CHAIR_STANDARD: SizeTemplate = SizeTemplate {
        name: "Standard Chair",
        category: TemplateCategory::Furniture,
        size: Vector3::new(0.5, 0.85, 0.5),
        description: "Standard dining chair",
    };

    pub const BED_SINGLE: SizeTemplate = SizeTemplate {
        name: "Single Bed",
        category: TemplateCategory::Furniture,
        size: Vector3::new(0.9, 0.5, 1.9),
        description: "Single bed: 90cm x 190cm",
    };

    pub const BED_DOUBLE: SizeTemplate = SizeTemplate {
        name: "Double Bed",
        category: TemplateCategory::Furniture,
        size: Vector3::new(1.4, 0.5, 1.9),
        description: "Double bed: 140cm x 190cm",
    };

    pub const DESK: SizeTemplate = SizeTemplate {
        name: "Desk",
        category: TemplateCategory::Furniture,
        size: Vector3::new(1.2, 0.75, 0.6),
        description: "Standard office desk",
    };

    pub const SHELF_BOOKCASE: SizeTemplate = SizeTemplate {
        name: "Bookcase",
        category: TemplateCategory::Furniture,
        size: Vector3::new(0.8, 1.8, 0.3),
        description: "Standard bookcase",
    };
}

/// Vehicle templates
pub mod vehicle {
    use super::*;

    pub const CAR_SEDAN: SizeTemplate = SizeTemplate {
        name: "Sedan",
        category: TemplateCategory::Vehicle,
        size: Vector3::new(1.8, 1.5, 4.5),
        description: "Average sedan: 4.5m long",
    };

    pub const CAR_SUV: SizeTemplate = SizeTemplate {
        name: "SUV",
        category: TemplateCategory::Vehicle,
        size: Vector3::new(2.0, 1.8, 5.0),
        description: "Large SUV: 5.0m long",
    };

    pub const BIKE: SizeTemplate = SizeTemplate {
        name: "Bicycle",
        category: TemplateCategory::Vehicle,
        size: Vector3::new(0.6, 1.1, 1.8),
        description: "Standard bicycle",
    };

    pub const TRUCK: SizeTemplate = SizeTemplate {
        name: "Pickup Truck",
        category: TemplateCategory::Vehicle,
        size: Vector3::new(2.0, 1.8, 5.5),
        description: "Full-size pickup truck",
    };
}

/// Common props
pub mod props {
    use super::*;

    pub const CRATE_SMALL: SizeTemplate = SizeTemplate {
        name: "Small Crate",
        category: TemplateCategory::Prop,
        size: Vector3::new(0.5, 0.5, 0.5),
        description: "50cm cube crate",
    };

    pub const CRATE_LARGE: SizeTemplate = SizeTemplate {
        name: "Large Crate",
        category: TemplateCategory::Prop,
        size: Vector3::new(1.0, 1.0, 1.0),
        description: "1m cube crate",
    };

    pub const BARREL: SizeTemplate = SizeTemplate {
        name: "Barrel",
        category: TemplateCategory::Prop,
        size: Vector3::new(0.6, 0.85, 0.6),
        description: "Standard 55-gallon drum",
    };

    pub const LAMP_POST: SizeTemplate = SizeTemplate {
        name: "Lamp Post",
        category: TemplateCategory::Prop,
        size: Vector3::new(0.2, 3.5, 0.2),
        description: "Street lamp post",
    };

    pub const TRAFFIC_CONE: SizeTemplate = SizeTemplate {
        name: "Traffic Cone",
        category: TemplateCategory::Prop,
        size: Vector3::new(0.3, 0.7, 0.3),
        description: "Standard traffic cone",
    };
}

/// Environment templates
pub mod environment {
    use super::*;

    pub const TREE_SMALL: SizeTemplate = SizeTemplate {
        name: "Small Tree",
        category: TemplateCategory::Environment,
        size: Vector3::new(2.0, 3.0, 2.0),
        description: "Young tree: 3m tall",
    };

    pub const TREE_LARGE: SizeTemplate = SizeTemplate {
        name: "Large Tree",
        category: TemplateCategory::Environment,
        size: Vector3::new(8.0, 15.0, 8.0),
        description: "Mature tree: 15m tall",
    };

    pub const ROCK_SMALL: SizeTemplate = SizeTemplate {
        name: "Small Rock",
        category: TemplateCategory::Environment,
        size: Vector3::new(0.5, 0.4, 0.6),
        description: "Small boulder",
    };

    pub const ROCK_LARGE: SizeTemplate = SizeTemplate {
        name: "Large Rock",
        category: TemplateCategory::Environment,
        size: Vector3::new(3.0, 2.5, 3.5),
        description: "Large boulder",
    };

    pub const TERRAIN_CHUNK: SizeTemplate = SizeTemplate {
        name: "Terrain Chunk",
        category: TemplateCategory::Environment,
        size: Vector3::new(100.0, 10.0, 100.0),
        description: "Standard terrain tile: 100m x 100m",
    };
}

/// CAD Standard sizes
pub mod cad {
    use super::*;

    /// ISO A-series paper sizes (in meters for reference)
    pub const A4_PAPER: SizeTemplate = SizeTemplate {
        name: "A4 Paper",
        category: TemplateCategory::Prop,
        size: Vector3::new(0.210, 0.001, 0.297),
        description: "ISO A4: 210mm x 297mm",
    };

    pub const A3_PAPER: SizeTemplate = SizeTemplate {
        name: "A3 Paper",
        category: TemplateCategory::Prop,
        size: Vector3::new(0.297, 0.001, 0.420),
        description: "ISO A3: 297mm x 420mm",
    };

    /// Standard metric dimensions
    pub const METRIC_UNIT_CUBE: SizeTemplate = SizeTemplate {
        name: "1m Cube",
        category: TemplateCategory::Prop,
        size: Vector3::new(1.0, 1.0, 1.0),
        description: "1 meter reference cube",
    };

    /// Standard imperial dimensions
    pub const FOOT_CUBE: SizeTemplate = SizeTemplate {
        name: "1ft Cube",
        category: TemplateCategory::Prop,
        size: Vector3::new(0.3048, 0.3048, 0.3048),
        description: "1 foot reference cube",
    };
}

/// All templates in one collection
pub fn all_templates() -> Vec<SizeTemplate> {
    vec![
        // Characters
        character::HUMAN_MALE,
        character::HUMAN_FEMALE,
        character::CHILD,
        character::CAPSULE_COLLISION,
        // Architecture
        architecture::DOOR_STANDARD,
        architecture::DOOR_DOUBLE,
        architecture::WALL_INTERIOR,
        architecture::WALL_EXTERIOR,
        architecture::WINDOW_STANDARD,
        architecture::STAIRS_STEP,
        architecture::CEILING_RESIDENTIAL,
        architecture::CEILING_COMMERCIAL,
        // Furniture
        furniture::TABLE_DINING,
        furniture::CHAIR_STANDARD,
        furniture::BED_SINGLE,
        furniture::BED_DOUBLE,
        furniture::DESK,
        furniture::SHELF_BOOKCASE,
        // Vehicles
        vehicle::CAR_SEDAN,
        vehicle::CAR_SUV,
        vehicle::BIKE,
        vehicle::TRUCK,
        // Props
        props::CRATE_SMALL,
        props::CRATE_LARGE,
        props::BARREL,
        props::LAMP_POST,
        props::TRAFFIC_CONE,
        // Environment
        environment::TREE_SMALL,
        environment::TREE_LARGE,
        environment::ROCK_SMALL,
        environment::ROCK_LARGE,
        environment::TERRAIN_CHUNK,
        // CAD
        cad::A4_PAPER,
        cad::A3_PAPER,
        cad::METRIC_UNIT_CUBE,
        cad::FOOT_CUBE,
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_unit_conversion() {
        let meters = Unit::Meters.to_meters(1.0);
        let cm = Unit::Centimeters.to_meters(100.0);
        assert!((meters - cm).abs() < 0.001);
    }

    #[test]
    fn test_template_engine_conversion() {
        let door = architecture::DOOR_STANDARD;
        let unity_size = door.for_unity();
        let unreal_size = door.for_unreal();

        // Unreal should be 100x Unity (cm vs m)
        assert!((unreal_size.y / unity_size.y - 100.0).abs() < 0.1);
    }

    #[test]
    fn test_all_templates() {
        let templates = all_templates();
        assert!(templates.len() >= 30);
    }
}

/// MetaHuman and SDK-based templates
pub mod metahuman {
    use super::*;

    /// Epic MetaHuman proportions (realistic human)
    pub const METAHUMAN_MALE: SizeTemplate = SizeTemplate {
        name: "MetaHuman Male",
        category: TemplateCategory::Character,
        size: Vector3::new(0.45, 1.82, 0.28),
        description: "Epic MetaHuman male: 182cm, realistic proportions",
    };

    pub const METAHUMAN_FEMALE: SizeTemplate = SizeTemplate {
        name: "MetaHuman Female",
        category: TemplateCategory::Character,
        size: Vector3::new(0.42, 1.68, 0.26),
        description: "Epic MetaHuman female: 168cm, realistic proportions",
    };

    /// Ready Player Me (VR avatar standard)
    pub const RPM_AVATAR: SizeTemplate = SizeTemplate {
        name: "Ready Player Me Avatar",
        category: TemplateCategory::Character,
        size: Vector3::new(0.40, 1.75, 0.25),
        description: "RPM avatar standard: optimized for VR/metaverse",
    };

    /// VRChat avatar limits
    pub const VRCHAT_MEDIUM: SizeTemplate = SizeTemplate {
        name: "VRChat Medium",
        category: TemplateCategory::Character,
        size: Vector3::new(0.35, 1.60, 0.23),
        description: "VRChat medium avatar (performance rating)",
    };

    /// Unity Standard Assets Third Person
    pub const UNITY_THIRD_PERSON: SizeTemplate = SizeTemplate {
        name: "Unity Third Person Controller",
        category: TemplateCategory::Character,
        size: Vector3::new(0.40, 1.80, 0.25),
        description: "Unity Standard Assets character controller",
    };

    /// Unreal Mannequin (UE4/UE5 default)
    pub const UE_MANNEQUIN: SizeTemplate = SizeTemplate {
        name: "UE Mannequin",
        category: TemplateCategory::Character,
        size: Vector3::new(0.42, 1.83, 0.26),
        description: "Unreal Engine default mannequin (183cm)",
    };
}

/// Game-specific templates from popular titles
pub mod game_standards {
    use super::*;

    /// Half-Life/Source Engine
    pub const HL_PLAYER: SizeTemplate = SizeTemplate {
        name: "Half-Life Player",
        category: TemplateCategory::Character,
        size: Vector3::new(0.40, 1.83, 0.30),
        description: "Half-Life player (72 units tall in Source)",
    };

    /// Quake/id Tech
    pub const QUAKE_PLAYER: SizeTemplate = SizeTemplate {
        name: "Quake Player",
        category: TemplateCategory::Character,
        size: Vector3::new(0.40, 1.78, 0.30),
        description: "Quake player dimensions",
    };

    /// Minecraft block
    pub const MINECRAFT_BLOCK: SizeTemplate = SizeTemplate {
        name: "Minecraft Block",
        category: TemplateCategory::Prop,
        size: Vector3::new(1.0, 1.0, 1.0),
        description: "Minecraft 1m cube block",
    };

    /// Roblox stud (unit)
    pub const ROBLOX_STUD: SizeTemplate = SizeTemplate {
        name: "Roblox Stud",
        category: TemplateCategory::Prop,
        size: Vector3::new(0.28, 0.28, 0.28),
        description: "Roblox stud: 28cm (0.28m)",
    };
}

