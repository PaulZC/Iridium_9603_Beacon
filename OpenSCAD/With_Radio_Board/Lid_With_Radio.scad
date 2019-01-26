// Simple Lid for the Iridium Beacon Cover with Radio Board

$fn=50; // fragments
wall = 2; // cover wall thickness
thickness = 2; // lid end thickness
internal_width = 60; // internal width (X) of the cover
internal_depth = 35; // internal depth (Y) of the cover
gap = 0.3; // clearance gap (per side)
insert_height = 3; // extra height for the lid insert
internal_corner_radius = 1.0; // radius of the internal corner cylinder

sma_r = 3.75; // radius of the hole for the sma connector
sma_x_sep = 1.266 * 25.4; // X separation of the two SMA connectors
sma_y_offset = 0.5; // y offset of the holes for the sma connectors w.r.t. the Y center of the void
sma_wall_thickness = 3.0; // wall thickness around the SMA connectors

relay_recess_width = 20.0; // width of the recess for the relay terminals
relay_wall_thickness = 1.5; // wall thickness across the relay recess

support_x_offset = 4.0; // x offset of the support w.r.t. the X center of the void
support_width = 2.0; // x width of the support
support_depth = 2.0; // y depth of the support

if (gap > internal_corner_radius) echo("Error! Gap cannot be greater than the internal corner radius!");

width = internal_width + (2 * wall); // lid external width (X)
depth = internal_depth + (2 * wall); // lid external depth (Y)

total_height = wall + insert_height; // total height of the lid

sma_1_x = (width / 2) - (sma_x_sep / 2); // x position of sma connector 1
sma_2_x = (width / 2) + (sma_x_sep / 2); // x position of sma connector 2
sma_y = (depth / 2) + sma_y_offset; // y position of the sma connectors

external_corner_radius = internal_corner_radius + wall; // external corner radius

module outer()
{
    translate([external_corner_radius, external_corner_radius, 0])
        minkowski() {
            cube([(width - (2 * external_corner_radius)), (depth - (2 * external_corner_radius)), (thickness / 2)]);
            cylinder(h=(thickness / 2), r=external_corner_radius);
        }
}

module inner()
// Thicker than required to avoid zero thickness joints
{
    translate([external_corner_radius, external_corner_radius, 0])
        minkowski() {
            cube([(width - (2 * external_corner_radius)), (depth - (2 * external_corner_radius)), (total_height / 2)]);
            cylinder(h=(total_height / 2), r=(internal_corner_radius - gap));
        }
}

module recess()
// Thicker than required to avoid zero thickness joints
{
    translate([(internal_corner_radius + wall + wall), (internal_corner_radius + wall + wall), sma_wall_thickness])
        minkowski() {
            cube([(width - (2 * (wall + wall + internal_corner_radius))), (depth - (2 * (wall + wall + internal_corner_radius))), (total_height / 2)]);
            cylinder(h=(total_height / 2), r=internal_corner_radius);
        }
}

module lid()
{
    union() {
        outer();
        inner();
    }
}

module sma_1()
// Cylinder is taller than required to avoid zero thickness skins
{
    translate([sma_1_x, sma_y, -1]) {
        cylinder(h=(total_height + 2),r=sma_r);
    }
}

module sma_2()
// Cylinder is taller than required to avoid zero thickness skins
{
    translate([sma_2_x, sma_y, -1]) {
        cylinder(h=(total_height + 2),r=sma_r);
    }
}

module pcb_slot()
// Cube is taller amd wider than required to avoid zero thickness skins
{
    translate([0, (sma_y - sma_r), sma_wall_thickness]) {
        cube([width, (sma_r * 2), total_height]);
    }
}

module relay_recess()
// Recess is higher than required to avoid zero thickness skins
{
    translate([((width / 2) - (relay_recess_width / 2)), (2 * wall), relay_wall_thickness]) {
        cube([relay_recess_width, (depth - (4 * wall)), total_height]);
    }
}

module support()
{
    translate([((width / 2) + support_x_offset - (support_width / 2)),(depth - ((2 * wall) + support_depth)), 0]) {
        cube([support_width, support_depth, total_height]);
    }
}

module finished_lid()
{
    union() {
        difference() {
            lid();
            sma_1();
            sma_2();
            recess();
            pcb_slot();
            relay_recess();
        }
        support();
    }
}

finished_lid();
