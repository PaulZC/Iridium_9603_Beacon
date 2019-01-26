// Simple Cover for the Iridium Beacon with Radio Board

$fn=50; // fragments
wall = 2.0; // wall thickness
internal_width = 60.0; // internal width (X) of the cover
internal_depth = 35.0; // internal depth (Y) of the cover
internal_height = 78.0; // internal height (Z) of the cover
lid_insert = 1.0; // extra height for the lid insert

internal_corner_radius = 1.0; // radius of the internal corner cylinder

support_x_offset = 4.0; // x offset of the support w.r.t. the X center of the void
support_width = 2.0; // x width of the support
support_depth = 2.0; // y depth of the support
support_height = 55.0; // z height of the support

height = internal_height + wall + lid_insert; // cover external height (Z)
width = internal_width + (2 * wall); // cover external width (X)
depth = internal_depth + (2 * wall); // cover external depth (Y)

external_corner_radius = internal_corner_radius + wall; // external corner radius

module cover()
{
    translate([external_corner_radius, external_corner_radius, 0])
        minkowski() {
            cube([(width - (2 * external_corner_radius)), (depth - (2 * external_corner_radius)), (height / 2)]);
            cylinder(h=(height / 2), r=external_corner_radius);
        }
}

module void()
// Void will be higher than required to avoid zero thickness skin across opening
{
    translate([external_corner_radius, external_corner_radius, wall])
        minkowski() {
            cube([(internal_width - (2 * internal_corner_radius)), (internal_depth - (2 * internal_corner_radius)), (height / 2)]);
            cylinder(h=(height / 2), r=internal_corner_radius);
        }
}

module support()
{
    translate([((width / 2) + support_x_offset - (support_width / 2)),wall, 0]) {
        cube([support_width, support_depth, (support_height + wall)]);
    }
}

module finished_cover()
{
    union() {
        difference() {
            cover();
            void();
        }
        support();
    }
}

finished_cover();

