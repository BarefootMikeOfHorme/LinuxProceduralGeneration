// ==================================================================
// VaultMind Forge - Smart Primitives Library
// ==================================================================
// Smart OpenSCAD modules with multi-mode, unit scaling, and presets
//
// Each primitive is a "smart object" that can be:
// - Multiple shape variations in one module
// - Unit-aware (mm/cm/m) with automatic scaling
// - Preset-based (traffic_cone, basketball, etc.)
// - Resolution-controlled (smoothness)
//

// ==================================================================
// CONE - Smart Cone Module
// ==================================================================
module cone_smart(
    radius=10,           // [1:100] base radius
    height=20,           // [1:100] cone height
    unit="mm",           // [mm:cm:m] unit selector
    mode="cone",         // [cone:traffic_cone:wizard_hat:ice_cream:party_hat:full] shape mode
    resolution=32        // [6:256] number of segments
) {
    // Unit conversion
    scale_unit = (unit=="mm") ? 1 : (unit=="cm") ? 10 : (unit=="m") ? 1000 : 1;
    r_scaled = radius * scale_unit;
    h_scaled = height * scale_unit;

    if (mode == "cone") {
        // Standard cone
        cylinder(h=h_scaled, r1=r_scaled, r2=0, center=true, $fn=resolution);
    }

    if (mode == "traffic_cone") {
        // Traffic cone preset
        r_cone = 30 * scale_unit;
        h_cone = 70 * scale_unit;
        cylinder(h=h_cone, r1=r_cone, r2=0, center=true, $fn=resolution);
    }

    if (mode == "wizard_hat") {
        // Tall wizard hat preset
        r_hat = 40 * scale_unit;
        h_hat = 120 * scale_unit;
        cylinder(h=h_hat, r1=r_hat, r2=0, center=true, $fn=resolution);
    }

    if (mode == "ice_cream") {
        // Ice cream cone preset (upside down)
        r_ice = 25 * scale_unit;
        h_ice = 60 * scale_unit;
        rotate([180, 0, 0])
            cylinder(h=h_ice, r1=r_ice, r2=0, center=true, $fn=resolution);
    }

    if (mode == "party_hat") {
        // Party hat preset (bright colored)
        r_party = 35 * scale_unit;
        h_party = 80 * scale_unit;
        cylinder(h=h_party, r1=r_party, r2=0, center=true, $fn=resolution);
    }

    if (mode == "full") {
        // Full double cone (diamond shape)
        union() {
            cylinder(h=h_scaled, r1=r_scaled, r2=0, center=false, $fn=resolution);
            rotate([180, 0, 0])
                cylinder(h=h_scaled, r1=r_scaled, r2=0, center=false, $fn=resolution);
        }
    }
}

// Default render
cone_smart(radius=10, height=20, mode="cone", resolution=32);


// ==================================================================
// TORUS - Smart Torus Module
// ==================================================================
module torus_smart(
    major_radius=20,     // [5:100] outer ring radius
    minor_radius=5,      // [1:50] tube thickness
    unit="mm",           // [mm:cm:m] unit selector
    mode="torus",        // [torus:donut:tire:ring:life_preserver:halo] shape mode
    major_res=48,        // [6:128] outer ring smoothness
    minor_res=24         // [6:128] tube smoothness
) {
    // Unit conversion
    scale_unit = (unit=="mm") ? 1 : (unit=="cm") ? 10 : (unit=="m") ? 1000 : 1;
    maj_r = major_radius * scale_unit;
    min_r = minor_radius * scale_unit;

    if (mode == "torus") {
        // Standard torus
        rotate_extrude($fn=major_res)
            translate([maj_r, 0, 0])
                circle(r=min_r, $fn=minor_res);
    }

    if (mode == "donut") {
        // Food donut preset
        maj = 50 * scale_unit;
        min = 15 * scale_unit;
        rotate_extrude($fn=48)
            translate([maj, 0, 0])
                circle(r=min, $fn=24);
    }

    if (mode == "tire") {
        // Car tire preset
        maj = 100 * scale_unit;
        min = 20 * scale_unit;
        rotate_extrude($fn=64)
            translate([maj, 0, 0])
                circle(r=min, $fn=32);
    }

    if (mode == "ring") {
        // Jewelry ring preset
        maj = 8 * scale_unit;
        min = 1 * scale_unit;
        rotate_extrude($fn=64)
            translate([maj, 0, 0])
                circle(r=min, $fn=16);
    }

    if (mode == "life_preserver") {
        // Life preserver preset
        maj = 150 * scale_unit;
        min = 30 * scale_unit;
        rotate_extrude($fn=48)
            translate([maj, 0, 0])
                circle(r=min, $fn=24);
    }

    if (mode == "halo") {
        // Angel halo preset (thin ring)
        maj = 40 * scale_unit;
        min = 3 * scale_unit;
        rotate_extrude($fn=64)
            translate([maj, 0, 0])
                circle(r=min, $fn=16);
    }
}

// Default render (commented to avoid conflict)
// torus_smart(major_radius=20, minor_radius=5, mode="torus");


// ==================================================================
// CAPSULE - Smart Capsule Module
// ==================================================================
module capsule_smart(
    radius=5,            // [1:50] capsule thickness
    height=20,           // [1:100] capsule length
    unit="mm",           // [mm:cm:m] unit selector
    mode="capsule",      // [capsule:pill:bullet:rolling_pin:test_tube] shape mode
    resolution=32        // [6:128] smoothness
) {
    // Unit conversion
    scale_unit = (unit=="mm") ? 1 : (unit=="cm") ? 10 : (unit=="m") ? 1000 : 1;
    r_scaled = radius * scale_unit;
    h_scaled = height * scale_unit;

    if (mode == "capsule") {
        // Standard capsule
        union() {
            cylinder(h=h_scaled, r=r_scaled, center=true, $fn=resolution);
            translate([0, 0, h_scaled/2])
                sphere(r=r_scaled, $fn=resolution);
            translate([0, 0, -h_scaled/2])
                sphere(r=r_scaled, $fn=resolution);
        }
    }

    if (mode == "pill") {
        // Medicine pill preset
        r_pill = 3 * scale_unit;
        h_pill = 10 * scale_unit;
        union() {
            cylinder(h=h_pill, r=r_pill, center=true, $fn=32);
            translate([0, 0, h_pill/2])
                sphere(r=r_pill, $fn=32);
            translate([0, 0, -h_pill/2])
                sphere(r=r_pill, $fn=32);
        }
    }

    if (mode == "bullet") {
        // Bullet preset
        r_bullet = 4 * scale_unit;
        h_bullet = 15 * scale_unit;
        union() {
            cylinder(h=h_bullet, r=r_bullet, center=true, $fn=32);
            translate([0, 0, h_bullet/2])
                sphere(r=r_bullet, $fn=32);
            translate([0, 0, -h_bullet/2])
                sphere(r=r_bullet, $fn=32);
        }
    }

    if (mode == "rolling_pin") {
        // Rolling pin preset
        r_pin = 15 * scale_unit;
        h_pin = 80 * scale_unit;
        union() {
            cylinder(h=h_pin, r=r_pin, center=true, $fn=48);
            translate([0, 0, h_pin/2])
                sphere(r=r_pin, $fn=48);
            translate([0, 0, -h_pin/2])
                sphere(r=r_pin, $fn=48);
        }
    }

    if (mode == "test_tube") {
        // Test tube preset
        r_tube = 6 * scale_unit;
        h_tube = 40 * scale_unit;
        union() {
            cylinder(h=h_tube, r=r_tube, center=true, $fn=32);
            translate([0, 0, h_tube/2])
                sphere(r=r_tube, $fn=32);
        }
    }
}

// Default render (commented)
// capsule_smart(radius=5, height=20, mode="capsule");


// ==================================================================
// TUBE - Smart Tube Module (Hollow Cylinder)
// ==================================================================
module tube_smart(
    outer_radius=15,     // [2:100] outer radius
    inner_radius=10,     // [1:99] inner radius
    height=30,           // [1:200] tube height
    unit="mm",           // [mm:cm:m] unit selector
    mode="tube",         // [tube:pipe:straw:chimney:tunnel] shape mode
    resolution=48        // [6:128] smoothness
) {
    // Unit conversion
    scale_unit = (unit=="mm") ? 1 : (unit=="cm") ? 10 : (unit=="m") ? 1000 : 1;
    r_out = outer_radius * scale_unit;
    r_in = inner_radius * scale_unit;
    h_scaled = height * scale_unit;

    if (mode == "tube") {
        // Standard tube
        difference() {
            cylinder(h=h_scaled, r=r_out, center=true, $fn=resolution);
            cylinder(h=h_scaled+1, r=r_in, center=true, $fn=resolution);
        }
    }

    if (mode == "pipe") {
        // Metal pipe preset
        r_out_pipe = 20 * scale_unit;
        r_in_pipe = 17 * scale_unit;
        h_pipe = 100 * scale_unit;
        difference() {
            cylinder(h=h_pipe, r=r_out_pipe, center=true, $fn=64);
            cylinder(h=h_pipe+1, r=r_in_pipe, center=true, $fn=64);
        }
    }

    if (mode == "straw") {
        // Drinking straw preset
        r_out_straw = 3 * scale_unit;
        r_in_straw = 2.5 * scale_unit;
        h_straw = 150 * scale_unit;
        difference() {
            cylinder(h=h_straw, r=r_out_straw, center=true, $fn=32);
            cylinder(h=h_straw+1, r=r_in_straw, center=true, $fn=32);
        }
    }

    if (mode == "chimney") {
        // Chimney preset
        r_out_chim = 50 * scale_unit;
        r_in_chim = 45 * scale_unit;
        h_chim = 200 * scale_unit;
        difference() {
            cylinder(h=h_chim, r=r_out_chim, center=true, $fn=48);
            cylinder(h=h_chim+1, r=r_in_chim, center=true, $fn=48);
        }
    }

    if (mode == "tunnel") {
        // Tunnel preset (rotated)
        r_out_tunnel = 100 * scale_unit;
        r_in_tunnel = 90 * scale_unit;
        h_tunnel = 500 * scale_unit;
        rotate([90, 0, 0])
            difference() {
                cylinder(h=h_tunnel, r=r_out_tunnel, center=true, $fn=64);
                cylinder(h=h_tunnel+1, r=r_in_tunnel, center=true, $fn=64);
            }
    }
}

// Default render (commented)
// tube_smart(outer_radius=15, inner_radius=10, height=30, mode="tube");


// ==================================================================
// DOME - Smart Dome Module (Hemisphere)
// ==================================================================
module dome_smart(
    radius=20,           // [1:100] dome radius
    unit="mm",           // [mm:cm:m] unit selector
    mode="dome",         // [dome:helmet:igloo:half_ball:observatory] shape mode
    resolution=64        // [6:256] smoothness
) {
    // Unit conversion
    scale_unit = (unit=="mm") ? 1 : (unit=="cm") ? 10 : (unit=="m") ? 1000 : 1;
    r_scaled = radius * scale_unit;

    if (mode == "dome") {
        // Standard dome (half sphere)
        difference() {
            sphere(r=r_scaled, $fn=resolution);
            translate([0, 0, -r_scaled])
                cube([r_scaled*2+1, r_scaled*2+1, r_scaled*2], center=true);
        }
    }

    if (mode == "helmet") {
        // Helmet preset
        r_helmet = 100 * scale_unit;
        difference() {
            sphere(r=r_helmet, $fn=64);
            translate([0, 0, -r_helmet])
                cube([r_helmet*2+1, r_helmet*2+1, r_helmet*2], center=true);
        }
    }

    if (mode == "igloo") {
        // Igloo preset
        r_igloo = 150 * scale_unit;
        difference() {
            sphere(r=r_igloo, $fn=48);
            translate([0, 0, -r_igloo])
                cube([r_igloo*2+1, r_igloo*2+1, r_igloo*2], center=true);
        }
    }

    if (mode == "half_ball") {
        // Half ball preset
        r_ball = 50 * scale_unit;
        difference() {
            sphere(r=r_ball, $fn=64);
            translate([0, 0, -r_ball])
                cube([r_ball*2+1, r_ball*2+1, r_ball*2], center=true);
        }
    }

    if (mode == "observatory") {
        // Observatory dome preset
        r_obs = 500 * scale_unit;
        difference() {
            sphere(r=r_obs, $fn=128);
            translate([0, 0, -r_obs])
                cube([r_obs*2+1, r_obs*2+1, r_obs*2], center=true);
        }
    }
}

// Default render (commented)
// dome_smart(radius=20, mode="dome");


// ==================================================================
// RING - Smart Ring Module (Flat Torus)
// ==================================================================
module ring_smart(
    outer_radius=20,     // [2:100] outer radius
    inner_radius=15,     // [1:99] inner radius
    thickness=2,         // [0.1:20] ring thickness
    unit="mm",           // [mm:cm:m] unit selector
    mode="ring",         // [ring:coin:washer:gasket:frame] shape mode
    resolution=64        // [6:256] smoothness
) {
    // Unit conversion
    scale_unit = (unit=="mm") ? 1 : (unit=="cm") ? 10 : (unit=="m") ? 1000 : 1;
    r_out = outer_radius * scale_unit;
    r_in = inner_radius * scale_unit;
    t_scaled = thickness * scale_unit;

    if (mode == "ring") {
        // Standard ring
        linear_extrude(height=t_scaled, center=true)
            difference() {
                circle(r=r_out, $fn=resolution);
                circle(r=r_in, $fn=resolution);
            }
    }

    if (mode == "coin") {
        // Coin preset
        r_out_coin = 25 * scale_unit;
        r_in_coin = 0 * scale_unit;
        t_coin = 2 * scale_unit;
        linear_extrude(height=t_coin, center=true)
            difference() {
                circle(r=r_out_coin, $fn=64);
                circle(r=r_in_coin, $fn=64);
            }
    }

    if (mode == "washer") {
        // Washer preset
        r_out_wash = 15 * scale_unit;
        r_in_wash = 8 * scale_unit;
        t_wash = 2 * scale_unit;
        linear_extrude(height=t_wash, center=true)
            difference() {
                circle(r=r_out_wash, $fn=48);
                circle(r=r_in_wash, $fn=48);
            }
    }

    if (mode == "gasket") {
        // Gasket preset
        r_out_gas = 50 * scale_unit;
        r_in_gas = 45 * scale_unit;
        t_gas = 3 * scale_unit;
        linear_extrude(height=t_gas, center=true)
            difference() {
                circle(r=r_out_gas, $fn=64);
                circle(r=r_in_gas, $fn=64);
            }
    }

    if (mode == "frame") {
        // Picture frame preset
        r_out_frame = 100 * scale_unit;
        r_in_frame = 80 * scale_unit;
        t_frame = 10 * scale_unit;
        linear_extrude(height=t_frame, center=true)
            difference() {
                circle(r=r_out_frame, $fn=64);
                circle(r=r_in_frame, $fn=64);
            }
    }
}

// Default render (commented)
// ring_smart(outer_radius=20, inner_radius=15, thickness=2, mode="ring");


// ==================================================================
// PYRAMID - Smart Pyramid Module
// ==================================================================
module pyramid_smart(
    base_size=20,        // [1:100] base size
    height=30,           // [1:100] pyramid height
    sides=4,             // [3:8] number of sides
    unit="mm",           // [mm:cm:m] unit selector
    mode="pyramid",      // [pyramid:egyptian:tent:obelisk:spike] shape mode
    resolution=1         // [1:4] subdivision level
) {
    // Unit conversion
    scale_unit = (unit=="mm") ? 1 : (unit=="cm") ? 10 : (unit=="m") ? 1000 : 1;
    b_scaled = base_size * scale_unit;
    h_scaled = height * scale_unit;

    if (mode == "pyramid") {
        // Standard pyramid
        cylinder(h=h_scaled, r1=b_scaled/2, r2=0, center=true, $fn=sides);
    }

    if (mode == "egyptian") {
        // Egyptian pyramid preset (4-sided, specific ratio)
        b_egypt = 100 * scale_unit;
        h_egypt = 75 * scale_unit;
        cylinder(h=h_egypt, r1=b_egypt/2, r2=0, center=true, $fn=4);
    }

    if (mode == "tent") {
        // Tent preset (4-sided, low profile)
        b_tent = 100 * scale_unit;
        h_tent = 50 * scale_unit;
        cylinder(h=h_tent, r1=b_tent/2, r2=0, center=true, $fn=4);
    }

    if (mode == "obelisk") {
        // Obelisk preset (4-sided, tall)
        b_obelisk = 20 * scale_unit;
        h_obelisk = 150 * scale_unit;
        cylinder(h=h_obelisk, r1=b_obelisk/2, r2=0, center=true, $fn=4);
    }

    if (mode == "spike") {
        // Spike preset (many sides, sharp)
        b_spike = 10 * scale_unit;
        h_spike = 40 * scale_unit;
        cylinder(h=h_spike, r1=b_spike/2, r2=0, center=true, $fn=16);
    }
}

// Default render (commented)
// pyramid_smart(base_size=20, height=30, sides=4, mode="pyramid");


// ==================================================================
// Example Usages (Uncomment to test)
// ==================================================================

// CONE EXAMPLES
// cone_smart(radius=30, height=70, mode="traffic_cone", unit="mm");
// cone_smart(radius=40, height=120, mode="wizard_hat", unit="mm");
// cone_smart(radius=10, height=20, mode="cone", resolution=64);

// TORUS EXAMPLES
// torus_smart(major_radius=50, minor_radius=15, mode="donut", unit="mm");
// torus_smart(major_radius=100, minor_radius=20, mode="tire", unit="mm");
// torus_smart(major_radius=8, minor_radius=1, mode="ring", unit="mm");

// CAPSULE EXAMPLES
// capsule_smart(radius=3, height=10, mode="pill", unit="mm");
// capsule_smart(radius=4, height=15, mode="bullet", unit="mm");
// capsule_smart(radius=15, height=80, mode="rolling_pin", unit="mm");

// TUBE EXAMPLES
// tube_smart(outer_radius=20, inner_radius=17, height=100, mode="pipe", unit="mm");
// tube_smart(outer_radius=3, inner_radius=2.5, height=150, mode="straw", unit="mm");

// DOME EXAMPLES
// dome_smart(radius=100, mode="helmet", unit="mm");
// dome_smart(radius=150, mode="igloo", unit="mm");

// RING EXAMPLES
// ring_smart(outer_radius=25, inner_radius=0, thickness=2, mode="coin", unit="mm");
// ring_smart(outer_radius=15, inner_radius=8, thickness=2, mode="washer", unit="mm");

// PYRAMID EXAMPLES
// pyramid_smart(base_size=100, height=75, sides=4, mode="egyptian", unit="mm");
// pyramid_smart(base_size=100, height=50, sides=4, mode="tent", unit="mm");
