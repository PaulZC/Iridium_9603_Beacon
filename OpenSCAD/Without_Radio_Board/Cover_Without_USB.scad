// Simple Cover for the Iridium Beacon without USB opening

$fn=50; // fragments
wall = 2.0; // wall thickness
end_wall = 3.0; // end wall thickness
internal_width = 60.0; // internal width (X) of the cover
internal_depth = 30.0; // internal depth (Y) of the cover
internal_height = 68.0; // internal height (Z) of the cover
lid_insert = 1.0; // extra height for the lid insert

internal_corner_radius = 1.0; // radius of the internal corner cylinder

support_x_offset = -4.0; // x offset of the support w.r.t. the X center of the void
support_width = 2.0; // x width of the support
support_depth = 1.0; // 1.5; // y depth of the support
support_height = 55.0; // z height of the support

usb_r = 4.0; // radius of the opening for the USB connector
usb_width = 14.0; // total width of the opening for the USB
usb_height = 2.0; // depth of the opening for the USB connector
usb_x_offset = 4.05; // X offset of the USB connector
usb_y_offset = 3.6; // y offset of the USB connector

height = internal_height + end_wall + lid_insert; // cover external height (Z)
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
    translate([external_corner_radius, external_corner_radius, end_wall])
        minkowski() {
            cube([(internal_width - (2 * internal_corner_radius)), (internal_depth - (2 * internal_corner_radius)), (height / 2)]);
            cylinder(h=(height / 2), r=internal_corner_radius);
        }
}

module usb_opening_end_1()
// Cylinder is taller than it needs to be to avoid zero thickness skins
{
    translate([((usb_width / 2) - usb_r),0,(end_wall - usb_height)]) {
        cylinder(h=end_wall,r=usb_r);
    }
}

module usb_opening_end_2()
// Cylinder is taller than it needs to be to avoid zero thickness skins
{
    translate([(0-((usb_width / 2) - usb_r)),0,(end_wall - usb_height)]) {
        cylinder(h=end_wall,r=usb_r);
    }
}

module usb_opening_mid()
// Cube is taller than it needs to be to avoid zero thickness skins
{
    translate([(-0.5 * (usb_width - (2 * usb_r))), (-0.5 * (2 * usb_r)), (end_wall - usb_height)]) {
        cube([(usb_width - (2 * usb_r)), (2 * usb_r), end_wall]);
    }
}

module usb()
{
    translate([((width / 2) + usb_x_offset), ((depth / 2) - usb_y_offset), 0]) {
        union() {
            usb_opening_end_1();
            usb_opening_end_2();
            usb_opening_mid();
        }
    }
}

module support()
{
    translate([((width / 2) + support_x_offset - (support_width / 2)),wall, 0]) {
        cube([support_width, support_depth, (support_height + end_wall)]);
    }
}

module finished_cover()
{
    union() {
        difference() {
            cover();
            void();
            usb();
        }
        support();
    }
}

finished_cover();

