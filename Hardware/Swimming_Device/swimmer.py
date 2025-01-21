import cadquery as cq

# Base shape: round disk with a diameter of 20cm and thickness of 5cm
diameter = 193  # Diameter in mm
disk_thickness = 25  # Thickness in mm
cutout_diameter = 50  # Diameter of the cutout in mm
fillet_radius = 12  # Radius for edge fillets

# Create the disk
disk = (
    cq.Workplane("XY")
    .circle(diameter / 2)
    .extrude(disk_thickness)
    .edges("%Circle").fillet(fillet_radius)  # Round the outer edges
)

# Create the cutout
cutout = (
    cq.Workplane("XY")
    .circle(cutout_diameter / 2)
    .extrude(disk_thickness)
)

# Subtract the cutout from the disk
final_disk = (
    disk
    .cut(cutout)
    .edges("not(%Plane)").fillet(fillet_radius)  # Round the edges of the cutout
)

# Export the STL file
cq.exporters.export(final_disk, 'swimmer.stl')