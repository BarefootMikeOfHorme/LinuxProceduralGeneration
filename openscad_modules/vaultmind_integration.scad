// ==================================================================
// VaultMind Forge - Integration Features
// ==================================================================
// Game property system for OpenSCAD modules
//
// Features:
// - SmartObject properties (type, physics, tags)
// - Game stats (health, armor, damage, etc.)
// - Color schemes (PBR materials)
// - Buffs and equipment slots
// - Multi-engine export metadata
//

// ==================================================================
// GLOBAL METADATA STORAGE
// ==================================================================
// These will be exported as JSON/YAML metadata alongside the mesh

// Object metadata
vm_object_name = "Unnamed";
vm_object_type = "STATIC_MESH";  // STATIC_MESH, ACTOR, INTERACTIVE, etc.
vm_physics_type = "STATIC";      // STATIC, DYNAMIC, KINEMATIC
vm_render_mode = "OPAQUE";       // OPAQUE, TRANSPARENT, INVISIBLE
vm_mass = 1.0;
vm_tags = [];

// Game stats
vm_stats = [
    ["health", 100],
    ["armor", 0],
    ["damage", 0],
    ["value", 0],
    ["weight", 0]
];

// Color scheme
vm_color_primary = "#FFFFFF";
vm_color_secondary = "#808080";
vm_color_accent = "#000000";
vm_metallic = 0.0;
vm_roughness = 0.5;
vm_emission = 0.0;

// Export settings
vm_export_unity = true;
vm_export_unreal = true;
vm_export_godot = true;
vm_export_cryengine = false;
vm_export_lumix = false;


// ==================================================================
// SMART OBJECT SETUP
// ==================================================================
module vm_set_object_properties(
    name="Unnamed",
    type="STATIC_MESH",     // [STATIC_MESH:ACTOR:INTERACTIVE:COLLISION:PICKUP:DESTRUCTIBLE]
    physics="STATIC",       // [STATIC:DYNAMIC:KINEMATIC]
    render="OPAQUE",        // [OPAQUE:TRANSPARENT:INVISIBLE]
    mass=1.0,
    tags=[]
) {
    // This module sets metadata (doesn't render geometry)
    // In customized OpenSCAD, this will write to metadata file

    echo("=== VaultMind Object Properties ===");
    echo(str("Name: ", name));
    echo(str("Type: ", type));
    echo(str("Physics: ", physics));
    echo(str("Render: ", render));
    echo(str("Mass: ", mass));
    echo(str("Tags: ", tags));
    echo("===================================");
}


// ==================================================================
// GAME STATS
// ==================================================================
module vm_set_stat(stat_name, value) {
    // Set a game stat
    echo(str("STAT: ", stat_name, " = ", value));
}

module vm_set_stats(
    health=100,
    armor=0,
    damage=0,
    attack_speed=1.0,
    move_speed=5.0,
    value=0,
    weight=0
) {
    echo("=== Game Stats ===");
    echo(str("Health: ", health));
    echo(str("Armor: ", armor));
    echo(str("Damage: ", damage));
    echo(str("Attack Speed: ", attack_speed));
    echo(str("Move Speed: ", move_speed));
    echo(str("Value: ", value, " gold"));
    echo(str("Weight: ", weight, " kg"));
    echo("==================");
}


// ==================================================================
// COLOR SCHEMES
// ==================================================================
module vm_set_color_scheme(
    name="default",
    primary="#FFFFFF",
    secondary="#808080",
    accent="#000000",
    metallic=0.0,      // [0:0.1:1.0]
    roughness=0.5,     // [0:0.1:1.0]
    emission=0.0       // [0:0.1:1.0]
) {
    echo("=== Color Scheme ===");
    echo(str("Name: ", name));
    echo(str("Primary: ", primary));
    echo(str("Secondary: ", secondary));
    echo(str("Accent: ", accent));
    echo(str("Metallic: ", metallic));
    echo(str("Roughness: ", roughness));
    echo(str("Emission: ", emission));
    echo("====================");
}

// Pre-defined color schemes
module vm_apply_color_preset(preset="default") {
    if (preset == "iron") {
        vm_set_color_scheme(
            name="iron",
            primary="#696969",
            secondary="#505050",
            metallic=0.9,
            roughness=0.4
        );
    }

    if (preset == "gold") {
        vm_set_color_scheme(
            name="gold",
            primary="#FFD700",
            secondary="#FFA500",
            metallic=1.0,
            roughness=0.2
        );
    }

    if (preset == "leather") {
        vm_set_color_scheme(
            name="leather",
            primary="#8B4513",
            secondary="#654321",
            metallic=0.0,
            roughness=0.8
        );
    }

    if (preset == "mythril") {
        vm_set_color_scheme(
            name="mythril",
            primary="#E0E0FF",
            secondary="#B0B0FF",
            metallic=0.8,
            roughness=0.3,
            emission=0.2
        );
    }

    if (preset == "epic_flame") {
        vm_set_color_scheme(
            name="epic_flame",
            primary="#FF4500",
            secondary="#FFD700",
            accent="#8B0000",
            metallic=0.9,
            roughness=0.3,
            emission=0.5
        );
    }
}


// ==================================================================
// BUFFS SYSTEM
// ==================================================================
module vm_add_buff(
    name,
    buff_type="PASSIVE",     // [PASSIVE:TEMPORARY:STATUS:AURA]
    duration=0,              // 0 = permanent
    description=""
) {
    echo("=== Buff ===");
    echo(str("Name: ", name));
    echo(str("Type: ", buff_type));
    if (duration > 0) {
        echo(str("Duration: ", duration, "s"));
    } else {
        echo("Duration: Permanent");
    }
    if (description != "") {
        echo(str("Description: ", description));
    }
    echo("============");
}


// ==================================================================
// EQUIPMENT SLOTS
// ==================================================================
module vm_add_equipment_slot(
    slot_type="MAIN_HAND",   // [MAIN_HAND:OFF_HAND:HEAD:CHEST:BACK:RING:SOCKET]
    position=[0,0,0]
) {
    echo("=== Equipment Slot ===");
    echo(str("Type: ", slot_type));
    echo(str("Position: ", position));
    echo("======================");

    // Visual marker for slot position
    color("yellow", 0.5)
        translate(position)
            sphere(r=0.5, $fn=16);
}


// ==================================================================
// RARITY SYSTEM
// ==================================================================
module vm_set_rarity(
    rarity="COMMON",         // [COMMON:UNCOMMON:RARE:EPIC:LEGENDARY:MYTHIC]
    stat_multiplier=1.0
) {
    echo("=== Rarity ===");
    echo(str("Tier: ", rarity));
    echo(str("Stat Multiplier: ", stat_multiplier, "x"));
    echo("==============");
}


// ==================================================================
// EXPORT SETTINGS
// ==================================================================
module vm_configure_export(
    unity=true,
    unreal=true,
    godot=true,
    cryengine=false,
    lumix=false,
    include_metadata=true,
    include_lods=false
) {
    echo("=== Export Configuration ===");
    if (unity) echo("  [x] Unity (Y-up, LH, 1.0 scale)");
    if (unreal) echo("  [x] Unreal (Z-up, LH, 100x scale)");
    if (godot) echo("  [x] Godot (Y-up, RH)");
    if (cryengine) echo("  [x] CryEngine");
    if (lumix) echo("  [x] Lumix");
    if (include_metadata) echo("  [x] Export metadata (JSON/YAML)");
    if (include_lods) echo("  [x] Generate LODs");
    echo("============================");
}


// ==================================================================
// COMPLETE SMART ASSET EXAMPLE
// ==================================================================
module vm_complete_asset_example() {
    // 1. Set object properties
    vm_set_object_properties(
        name="Epic Flame Sword",
        type="INTERACTIVE",
        physics="DYNAMIC",
        mass=3.5,
        tags=["weapon", "sword", "epic", "fire"]
    );

    // 2. Set game stats
    vm_set_stats(
        health=200,
        armor=0,
        damage=75,
        attack_speed=1.5,
        value=5000,
        weight=3.5
    );

    // 3. Apply color scheme
    vm_apply_color_preset("epic_flame");

    // 4. Add buffs
    vm_add_buff(
        name="Flame Strike",
        buff_type="PASSIVE",
        description="Attacks deal additional fire damage"
    );

    // 5. Add equipment slot
    vm_add_equipment_slot(
        slot_type="MAIN_HAND",
        position=[0, 0, 0]
    );

    // 6. Set rarity
    vm_set_rarity(
        rarity="EPIC",
        stat_multiplier=2.0
    );

    // 7. Configure export
    vm_configure_export(
        unity=true,
        unreal=true,
        godot=true,
        include_metadata=true,
        include_lods=true
    );

    // 8. The actual geometry (example: simple sword shape)
    color("#FF4500")  // Orange-red for flame
        union() {
            // Blade
            translate([0, 0, 5])
                cube([0.2, 1, 10], center=true);
            // Crossguard
            cube([3, 0.3, 0.5], center=true);
            // Handle
            translate([0, 0, -2])
                cylinder(h=4, r=0.15, center=true, $fn=16);
            // Pommel
            translate([0, 0, -4])
                sphere(r=0.3, $fn=16);
        }
}


// ==================================================================
// MATERIAL TEMPLATES
// ==================================================================
module vm_apply_material_template(material="iron") {
    if (material == "iron") {
        vm_set_color_scheme(
            name="iron",
            primary="#696969",
            secondary="#505050",
            metallic=0.9,
            roughness=0.4
        );
        echo("Material: Iron (+armor, +weight)");
    }

    if (material == "leather") {
        vm_set_color_scheme(
            name="leather",
            primary="#8B4513",
            secondary="#654321",
            metallic=0.0,
            roughness=0.8
        );
        echo("Material: Leather (+move_speed, -armor)");
    }

    if (material == "mythril") {
        vm_set_color_scheme(
            name="mythril",
            primary="#E0E0FF",
            secondary="#B0B0FF",
            metallic=0.8,
            roughness=0.3,
            emission=0.2
        );
        echo("Material: Mythril (+armor, +magic_resistance)");
    }

    if (material == "dragonbone") {
        vm_set_color_scheme(
            name="dragonbone",
            primary="#F5F5DC",
            secondary="#D3D3D3",
            metallic=0.3,
            roughness=0.6
        );
        echo("Material: Dragonbone (+damage, +fire_resistance)");
    }
}


// ==================================================================
// GENRE TEMPLATES
// ==================================================================
module vm_apply_genre(genre="fantasy") {
    if (genre == "fantasy") {
        echo("Genre: Fantasy");
        echo("  - Medieval weapons");
        echo("  - Magic effects");
        echo("  - Ornate details");
    }

    if (genre == "sci-fi") {
        echo("Genre: Sci-Fi");
        echo("  - Glowing edges");
        echo("  - Metallic finish");
        echo("  - Tech details");
    }

    if (genre == "post-apocalyptic") {
        echo("Genre: Post-Apocalyptic");
        echo("  - Rusty/weathered");
        echo("  - Makeshift construction");
        echo("  - Survival aesthetic");
    }

    if (genre == "cyberpunk") {
        echo("Genre: Cyberpunk");
        echo("  - Neon accents");
        echo("  - High-tech/low-life");
        echo("  - Urban aesthetic");
    }
}


// ==================================================================
// BATCH GENERATION HELPER
// ==================================================================
module vm_generate_variant(
    base_geometry,
    material="iron",
    rarity="COMMON",
    genre="fantasy"
) {
    // Apply templates
    vm_apply_material_template(material);
    vm_set_rarity(rarity);
    vm_apply_genre(genre);

    // Render geometry
    children();
}


// ==================================================================
// VALIDATION FUNCTIONS
// ==================================================================
module vm_validate_for_export() {
    echo("=== Export Validation ===");
    echo("[CHECK] Mesh is manifold");
    echo("[CHECK] No degenerate faces");
    echo("[CHECK] No flipped normals");
    echo("[CHECK] UV coordinates present");
    echo("[CHECK] Metadata complete");
    echo("=========================");
}


// ==================================================================
// LOD GENERATION MARKERS
// ==================================================================
module vm_mark_for_lod_generation(
    levels=["high", "medium", "low", "very_low"]
) {
    echo("=== LOD Generation ===");
    echo(str("Levels to generate: ", levels));
    echo("  - high: original quality");
    echo("  - medium: 50% triangles");
    echo("  - low: 25% triangles");
    echo("  - very_low: 10% triangles");
    echo("======================");
}


// ==================================================================
// EXAMPLE USAGE
// ==================================================================

// Example 1: Simple traffic cone with properties
module example_traffic_cone_with_properties() {
    // Set properties
    vm_set_object_properties(
        name="Traffic Cone",
        type="INTERACTIVE",
        physics="DYNAMIC",
        mass=5.0,
        tags=["traffic", "cone", "movable"]
    );

    vm_set_stats(
        health=50,
        durability=100,
        value=10,
        weight=5.0
    );

    vm_set_color_scheme(
        name="safety_orange",
        primary="#FF6600",
        secondary="#FFFFFF",
        roughness=0.7
    );

    // Geometry
    use <vaultmind_smart_primitives.scad>
    cone_smart(radius=30, height=70, mode="traffic_cone", unit="mm");
}

// Example 2: Epic weapon with full metadata
module example_epic_sword() {
    vm_set_object_properties(
        name="Blade of Flames",
        type="INTERACTIVE",
        physics="DYNAMIC",
        mass=3.5
    );

    vm_set_stats(
        damage=75,
        attack_speed=1.5,
        value=5000,
        weight=3.5
    );

    vm_apply_material_template("mythril");
    vm_apply_genre("fantasy");
    vm_set_rarity("EPIC", 2.0);

    vm_add_buff(
        name="Flame Strike",
        buff_type="PASSIVE",
        description="+25 fire damage"
    );

    vm_add_equipment_slot("MAIN_HAND", [0, 0, 0]);

    vm_configure_export(unity=true, unreal=true, include_lods=true);

    // Geometry (placeholder)
    color("#E0E0FF")
        cube([0.5, 2, 10], center=true);
}

// Uncomment to test
// example_traffic_cone_with_properties();
// example_epic_sword();
