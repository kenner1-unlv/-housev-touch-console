"""Build the first-fit enclosure for Waveshare ESP32-S3-Touch-LCD-7B.

Run with the FreeCAD Python console or FreeCADCmd.exe. Dimensions are mm.
Change the parameter block, then rerun to rebuild STEP, STL, and FCStd files.
"""

import os
import FreeCAD as App
import Part
import Import
from draftmake.make_shapestring import make_shapestring


# ------------------------------ Parameters ------------------------------
DISPLAY_W = 192.96
DISPLAY_H = 110.76
DISPLAY_CORNER_R = 7.88
DISPLAY_STACK = 18.40  # measured from Waveshare's 2025-10-25 STEP assembly
ACTIVE_W = 154.88
ACTIVE_H = 86.72

CASE_MARGIN = 8.0  # radial thickness added outside the display corner profile
CASE_W = DISPLAY_W + 2.0 * CASE_MARGIN
CASE_H = DISPLAY_H + 2.0 * CASE_MARGIN
FRONT_LIP = 2.4
REAR_Z = -19.70
PAN_TOP_Z = 0.80
BACK_WALL = 2.20
INNER_W = 195.00
INNER_H = 112.80
PAN_W = CASE_W
PAN_H = CASE_H
SCREEN_OPEN_W = ACTIVE_W + 1.5
SCREEN_OPEN_H = ACTIVE_H + 1.5
CORNER_R = DISPLAY_CORNER_R + CASE_MARGIN
WALL_R = CORNER_R
BOTTOM_R = DISPLAY_CORNER_R + 1.0

# Actual four PCB mount centers read from the Waveshare 7B assembly STEP.
# XY here is the front-view plane (X horizontal, Y vertical).
PCB_HOLES = [(-22.51, 22.07), (35.49, 22.07),
             (-22.51, -26.93), (35.49, -26.93)]
PCB_POST_R = 3.2
PCB_POST_TOP = -9.35
PCB_CLEAR_R = 1.40  # M2.5 clearance through rear plate and PCB support post
PCB_HEAD_R = 2.70   # recessed seat for a typical M2.5 screw head
PCB_HEAD_DEPTH = 1.50

# Four front-side M3 screws sit in the thick, rounded corner band. Their
# centers share the display corner arc center and lie outside the glass edge.
_corner_center_x = DISPLAY_W / 2.0 - DISPLAY_CORNER_R
_corner_center_y = DISPLAY_H / 2.0 - DISPLAY_CORNER_R
_corner_offset = (DISPLAY_CORNER_R + CASE_MARGIN / 2.0) / (2.0 ** 0.5)
SEAM_HOLES = [(-_corner_center_x - _corner_offset, _corner_center_y + _corner_offset),
              ( _corner_center_x + _corner_offset, _corner_center_y + _corner_offset),
              (-_corner_center_x - _corner_offset, -_corner_center_y - _corner_offset),
              ( _corner_center_x + _corner_offset, -_corner_center_y - _corner_offset)]
SEAM_POST_R = 4.0
SEAM_PILOT_R = 1.25  # M3 tapping pilot in the backing (2.5 mm diameter)
SEAM_PILOT_DEPTH = 7.0
SEAM_CLEAR_R = 1.70  # M3 clearance hole through the front bezel
SEAM_COUNTERBORE_R = 3.0  # 6 mm recessed seat for a typical M3 head
SEAM_COUNTERBORE_DEPTH = 2.0

# House V wordmark on the lower bezel band. Export the letter-shaped inlay as
# its own body so it can be assigned a second filament color in a slicer.
LOGO_TEXT = "HOUSE V"
LOGO_FONT = r"C:\Windows\Fonts\arialbd.ttf"
LOGO_SIZE = 8.0
LOGO_TRACKING = 0.8
LOGO_CENTER_Y = -53.5
LOGO_BADGE_W = 66.0
LOGO_BADGE_H = 12.0
LOGO_DEPTH = 0.75
LOGO_RECESS = 0.10

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def rounded_prism(cx, cy, z, width, height, depth, radius):
    """A box with rounded corners in its XY profile."""
    shape = Part.makeBox(width, height, depth,
                         App.Vector(cx - width / 2.0, cy - height / 2.0, z))
    vertical = []
    for edge in shape.Edges:
        verts = edge.Vertexes
        if len(verts) == 2:
            a, b = verts[0].Point, verts[1].Point
            if (abs(a.x - b.x) < 1e-7 and abs(a.y - b.y) < 1e-7
                    and abs(abs(a.z - b.z) - depth) < 1e-7):
                vertical.append(edge)
    if radius > 0 and vertical:
        shape = shape.makeFillet(radius, vertical)
    return shape


def cylinder_at(x, y, z, radius, height):
    return Part.makeCylinder(radius, height, App.Vector(x, y, z))


def add_dimension(obj, name, value, description):
    obj.addProperty("App::PropertyLength", name, "Design parameters", description)
    setattr(obj, name, value)


def make_rear_housing():
    pan_depth = PAN_TOP_Z - REAR_Z
    outer = rounded_prism(0, 0, REAR_Z, PAN_W, PAN_H, pan_depth, WALL_R)

    # The cavity leaves a 2.2 mm rear plate and a small clearance around the
    # 192.96 x 110.76 mm display assembly.
    cavity_z = REAR_Z + BACK_WALL
    cavity_depth = PAN_TOP_Z - cavity_z + 0.2
    cavity = rounded_prism(0, 0, cavity_z, INNER_W, INNER_H,
                           cavity_depth, BOTTOM_R)
    pan = outer.cut(cavity)

    # Board standoffs follow the four 58 x 49 mm hole locations in Waveshare's
    # board STEP. M2.5 clearance holes pass through the rear wall and standoffs;
    # shallow counterbores on the exterior recess the screw heads.
    for x, y in PCB_HOLES:
        post = cylinder_at(x, y, cavity_z, PCB_POST_R, PCB_POST_TOP - cavity_z)
        pan = pan.fuse(post)
    for x, y in PCB_HOLES:
        hole = cylinder_at(x, y, REAR_Z - 0.05,
                           PCB_CLEAR_R, PCB_POST_TOP - REAR_Z + 0.1)
        head_seat = cylinder_at(x, y, REAR_Z - 0.05,
                                PCB_HEAD_R, PCB_HEAD_DEPTH + 0.05)
        pan = pan.cut(hole).cut(head_seat)

    # Full-depth corner bosses take front-inserted M3 screws. The holes are
    # blind: the rear skin stays intact and the heads are recessed in the bezel.
    for x, y in SEAM_HOLES:
        boss = cylinder_at(x, y, REAR_Z + BACK_WALL, SEAM_POST_R,
                           PAN_TOP_Z - (REAR_Z + BACK_WALL))
        pan = pan.fuse(boss)
    for x, y in SEAM_HOLES:
        pilot = cylinder_at(x, y, PAN_TOP_Z - SEAM_PILOT_DEPTH,
                            SEAM_PILOT_R, SEAM_PILOT_DEPTH + 0.02)
        pan = pan.cut(pilot)

    return pan.removeSplitter()


def make_front_bezel():
    outer = rounded_prism(0, 0, PAN_TOP_Z, CASE_W, CASE_H,
                          FRONT_LIP, CORNER_R)
    aperture = rounded_prism(0, 0, PAN_TOP_Z - 0.1, SCREEN_OPEN_W,
                             SCREEN_OPEN_H, FRONT_LIP + 0.2, 2.0)
    bezel = outer.cut(aperture)

    # Through-clearance holes and recessed seats for screws inserted from the
    # display/front side into the blind pilots in the backing.
    for x, y in SEAM_HOLES:
        clear = cylinder_at(x, y, PAN_TOP_Z - 0.05,
                            SEAM_CLEAR_R, FRONT_LIP + 0.1)
        seat = cylinder_at(x, y,
                           PAN_TOP_Z + FRONT_LIP - SEAM_COUNTERBORE_DEPTH,
                           SEAM_COUNTERBORE_R, SEAM_COUNTERBORE_DEPTH + 0.05)
        bezel = bezel.cut(clear).cut(seat)

    logo_pocket, logo_inlay = make_logo_geometry()
    bezel = bezel.cut(logo_pocket)
    return bezel.removeSplitter(), logo_inlay


def make_logo_geometry():
    """Create a recessed badge with HOUSE V cut through its color inlay."""
    face_z = PAN_TOP_Z + FRONT_LIP
    text = make_shapestring(LOGO_TEXT, LOGO_FONT, LOGO_SIZE, LOGO_TRACKING)
    text.MakeFace = True
    doc.recompute()
    letter_profile = text.Shape.copy()
    doc.removeObject(text.Name)
    doc.recompute()

    bounds = letter_profile.BoundBox
    if bounds.XLength > LOGO_BADGE_W - 6.0 or bounds.YLength > LOGO_BADGE_H - 2.0:
        raise RuntimeError("HOUSE V wordmark (%.2f x %.2f mm) does not fit the logo badge" %
                           (bounds.XLength, bounds.YLength))
    letter_profile.translate(App.Vector(-bounds.Center.x,
                                        LOGO_CENTER_Y - bounds.Center.y,
                                        face_z - LOGO_DEPTH - 0.02))

    # Shrink the badge slightly in X/Y for realistic FDM fit clearance.
    inlay = rounded_prism(0, LOGO_CENTER_Y, face_z - LOGO_DEPTH,
                          LOGO_BADGE_W, LOGO_BADGE_H,
                          LOGO_DEPTH - LOGO_RECESS, 5.0)
    letters = letter_profile.copy()
    letters.translate(App.Vector(0, -LOGO_CENTER_Y,
                                 -(face_z - LOGO_DEPTH - 0.02)))
    fit = App.Matrix()
    fit.A11 = 0.99
    fit.A22 = 0.96
    letters = letters.transformGeometry(fit)
    letters.translate(App.Vector(0, LOGO_CENTER_Y,
                                 face_z - LOGO_DEPTH - 0.02))
    letter_cut = letters.extrude(App.Vector(
        0, 0, LOGO_DEPTH - LOGO_RECESS + 0.04))
    inlay = inlay.cut(letter_cut)
    inlay = inlay.removeSplitter()

    pocket = rounded_prism(0, LOGO_CENTER_Y, face_z - LOGO_DEPTH,
                           LOGO_BADGE_W, LOGO_BADGE_H,
                           LOGO_DEPTH + 0.03, 5.0)
    return pocket, inlay


def fail_if_invalid(name, shape):
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
        raise RuntimeError("%s is not a valid single solid (solids=%d, valid=%s)"
                           % (name, len(shape.Solids), shape.isValid()))


doc = App.newDocument("Waveshare_7B_Enclosure")
rear_shape = make_rear_housing()
bezel_shape, logo_shape = make_front_bezel()
fail_if_invalid("Rear housing", rear_shape)
fail_if_invalid("Front bezel", bezel_shape)
if logo_shape.isNull() or not logo_shape.isValid() or not logo_shape.Solids:
    raise RuntimeError("HOUSE V inlay is not a valid solid shape")

rear = doc.addObject("PartDesign::Feature", "RearHousing")
rear.Label = "Rear Housing - recessed M2.5 PCB mounts"
rear.Shape = rear_shape
if rear.ViewObject:
    rear.ViewObject.ShapeColor = (0.23, 0.26, 0.30)
add_dimension(rear, "DisplayEnvelopeWidth", DISPLAY_W, "Waveshare display width")
add_dimension(rear, "DisplayEnvelopeHeight", DISPLAY_H, "Waveshare display height")
add_dimension(rear, "DisplayStackDepth", DISPLAY_STACK, "Measured complete assembly depth")
add_dimension(rear, "HousingWidth", PAN_W, "Rear housing outer width")
add_dimension(rear, "HousingHeight", PAN_H, "Rear housing outer height")
add_dimension(rear, "CavityWidth", INNER_W, "Display cavity width")
add_dimension(rear, "CavityHeight", INNER_H, "Display cavity height")
add_dimension(rear, "RearWallThickness", BACK_WALL, "Rear plate thickness")
add_dimension(rear, "PCBStandoffHeight", PCB_POST_TOP - (REAR_Z + BACK_WALL),
              "PCB standoff height")

bezel = doc.addObject("PartDesign::Feature", "FrontBezel")
bezel.Label = "Front Bezel - screen aperture and HOUSE V recess"
bezel.Shape = bezel_shape
if bezel.ViewObject:
    bezel.ViewObject.ShapeColor = (0.10, 0.12, 0.15)
add_dimension(bezel, "OverallWidth", CASE_W, "Case face width")
add_dimension(bezel, "OverallHeight", CASE_H, "Case face height")
add_dimension(bezel, "ScreenOpeningWidth", SCREEN_OPEN_W, "Screen aperture width")
add_dimension(bezel, "ScreenOpeningHeight", SCREEN_OPEN_H, "Screen aperture height")
add_dimension(bezel, "BezelThickness", FRONT_LIP, "Bezel thickness")
add_dimension(bezel, "HouseVRecessDepth", LOGO_DEPTH, "HOUSE V logo pocket depth")

logo = doc.addObject("Part::Feature", "HouseVInlay")
logo.Label = "HOUSE V - second-color inlay"
logo.Shape = logo_shape
if logo.ViewObject:
    logo.ViewObject.ShapeColor = (0.88, 0.40, 0.10)
add_dimension(logo, "RecessClearance", 0.20, "Approximate XY fit allowance")

# Lightweight visual envelope only; the source Waveshare STEP is kept in vendor/.
# Its front face is at z=2.4 mm and it extends rearward by the measured 18.4 mm.
display = doc.addObject("Part::Feature", "DisplayReference")
display.Label = "Display reference envelope (not exported)"
display.Shape = rounded_prism(0, 0, PAN_TOP_Z + FRONT_LIP - DISPLAY_STACK,
                              DISPLAY_W, DISPLAY_H, DISPLAY_STACK, 7.88)
if display.ViewObject:
    display.ViewObject.ShapeColor = (0.12, 0.55, 0.72)
    display.ViewObject.Transparency = 82

doc.recompute()
App.setActiveDocument(doc.Name)
doc.recompute()

doc.saveAs(os.path.join(OUT_DIR, "Waveshare_7B_Enclosure.FCStd"))
Import.export([bezel, rear, logo], os.path.join(OUT_DIR, "Waveshare_7B_Enclosure.step"))

import MeshPart
for obj, filename in ((bezel, "Front_Bezel.stl"),
                      (rear, "Rear_Housing.stl"),
                      (logo, "HouseV_Inlay.stl")):
    mesh = MeshPart.meshFromShape(Shape=obj.Shape, LinearDeflection=0.15,
                                  AngularDeflection=0.35, Relative=False)
    mesh.write(os.path.join(OUT_DIR, filename))

report = [
    "Waveshare ESP32-S3-Touch-LCD-7B first-fit enclosure",
    "All dimensions in mm.",
    "Vendor assembly envelope: %.2f x %.2f x %.2f" %
    (DISPLAY_W, DISPLAY_H, DISPLAY_STACK),
    "Case envelope: %.2f x %.2f x %.2f" %
    (CASE_W, CASE_H, PAN_TOP_Z + FRONT_LIP - REAR_Z),
    "Rear housing: %d solid(s), valid=%s" % (len(rear_shape.Solids), rear_shape.isValid()),
    "Front bezel: %d solid(s), valid=%s" % (len(bezel_shape.Solids), bezel_shape.isValid()),
    "HOUSE V inlay: %d solid(s), valid=%s" % (len(logo_shape.Solids), logo_shape.isValid()),
    "PCB mount pattern: 58.00 x 49.00; centers (-22.51, 22.07), (35.49, 22.07), (-22.51, -26.93), (35.49, -26.93).",
    "Four M2.5 PCB mount holes pass through the rear plate and standoffs, with 5.4 mm x 1.5 mm recessed seats on the exterior.",
    "Four front-side M3 case-joining clearance holes have 6 mm x 2 mm head seats and blind pilots in rounded backing bosses.",
    "The lower bezel band has a %.2f mm deep HOUSE V recess; the matching inlay is exported as a separate STEP body and HouseV_Inlay.stl." % LOGO_DEPTH,
    "Connector access cutouts are intentionally omitted pending physical orientation/clearance confirmation.",
]
open(os.path.join(OUT_DIR, "build_report.txt"), "w").write("\n".join(report) + "\n")
print("\n".join(report))
