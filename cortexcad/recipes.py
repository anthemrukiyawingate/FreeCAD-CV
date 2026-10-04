"""Validated, deterministic FreeCAD-native lesson scripts (Python 3.11+).

Only finite numeric JSON data enters the source template. Creating a document is
deliberately non-idempotent: an existing lesson document blocks a replay.
"""

from __future__ import annotations

import json
import math
from textwrap import dedent, indent

PHASES: tuple[str, ...] = ("sketcher", "csg", "parametric", "capstone")
DEFAULTS: dict[str, dict[str, float]] = {
    "sketcher": {"length": 60.0, "width": 40.0, "height": 6.0},
    "csg": {"length": 40.0, "width": 30.0, "height": 12.0, "overlap": 15.0},
    "parametric": {"length": 60.0, "width": 40.0, "height": 6.0},
    "capstone": {
        "plate_length": 160.0, "plate_width": 100.0, "plate_thickness": 6.0,
        "mount_pitch_x": 100.0, "mount_pitch_y": 60.0,
        "fastener_diameter": 5.5, "edge_margin": 10.0, "bracket_height": 40.0,
        "sensor_length": 40.0, "sensor_width": 30.0, "sensor_height": 25.0,
        "clearance": 0.6, "wall": 3.0, "cable_diameter": 8.0, "lens_diameter": 12.0,
    },
}


def validate_parameters(
    phase: str, params: dict[str, object] | None = None
) -> dict[str, float]:
    """Normalize numeric millimetres; reject unknown keys and impossible fixtures.

    Partial dictionaries override teaching defaults. Physical acceptance requires
    a complete measurement record; this validator proves only bounded geometry.
    """
    if not isinstance(phase, str) or phase not in PHASES:
        raise ValueError(f"phase must be one of {', '.join(PHASES)}")
    if params is not None and not isinstance(params, dict):
        raise ValueError("parameters must be a JSON object")
    supplied: dict[str, object] = {} if params is None else params
    if set(supplied) - set(DEFAULTS[phase]):
        raise ValueError("unknown parameter keys; use the documented phase schema")
    normalized: dict[str, float] = {}
    for key, default in DEFAULTS[phase].items():
        value = supplied.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key} must be a numeric millimetre value, not a boolean or string")
        try:
            numeric = float(value)
        except (OverflowError, ValueError) as error:
            raise ValueError(f"{key} is outside the numeric range") from error
        maximum = 10.0 if key == "clearance" else 2000.0
        if not math.isfinite(numeric) or not 0.1 <= numeric <= maximum:
            raise ValueError(f"{key} must be finite and between 0.1 and {maximum:g} mm")
        normalized[key] = numeric
    p = normalized
    if phase == "csg" and not p["overlap"] < p["length"]:
        raise ValueError("overlap must be smaller than length for a partial intersection")
    if phase == "capstone":
        if min(p["mount_pitch_x"], p["mount_pitch_y"]) <= p["fastener_diameter"]:
            raise ValueError("mounting holes must be distinct and retain material between them")
        if p["edge_margin"] < max(p["plate_thickness"], p["fastener_diameter"]):
            raise ValueError("edge_margin must be at least plate_thickness and fastener_diameter")
        if p["mount_pitch_x"] + p["fastener_diameter"] + 2 * p["edge_margin"] > p["plate_length"]:
            raise ValueError("mount_pitch_x leaves insufficient plate edge material")
        if p["mount_pitch_y"] + p["fastener_diameter"] + 2 * (p["edge_margin"] + p["plate_thickness"]) > p["plate_width"]:
            raise ValueError("mount_pitch_y must clear the upright and plate edges")
        if p["bracket_height"] < p["fastener_diameter"] + 2 * p["edge_margin"]:
            raise ValueError("bracket_height leaves insufficient material around upright holes")
        inner_length = p["sensor_length"] + 2 * p["clearance"]
        inner_height = p["sensor_height"] + p["clearance"]
        if max(p["cable_diameter"], p["lens_diameter"]) + 2 * p["wall"] > min(inner_length, inner_height):
            raise ValueError("lens and cable apertures must retain wall material")
        if p["wall"] > 20 or p["plate_thickness"] >= p["plate_width"]:
            raise ValueError("wall or plate thickness exceeds the supported fixture envelope")
        if max(inner_length + 2 * p["wall"], p["sensor_width"] + 2 * p["clearance"] + 2 * p["wall"], inner_height + p["wall"]) > 2000:
            raise ValueError("housing outer dimensions must be at most 2000 mm")
    return normalized


_SKETCHER = '''
body: Any = doc.addObject("PartDesign::Body", "MountBody")
sketch: Any = doc.addObject("Sketcher::SketchObject", "MountProfile")
body.addObject(sketch)
length: float = p["length"]
width: float = p["width"]
points: list[Any] = [App.Vector(0, 0, 0), App.Vector(length, 0, 0),
                     App.Vector(length, width, 0), App.Vector(0, width, 0)]
for index in range(4):
    sketch.addGeometry(Part.LineSegment(points[index], points[(index + 1) % 4]), False)
constraints: list[Any] = [
    Sketcher.Constraint("Coincident", 0, 2, 1, 1),
    Sketcher.Constraint("Coincident", 1, 2, 2, 1),
    Sketcher.Constraint("Coincident", 2, 2, 3, 1),
    Sketcher.Constraint("Coincident", 3, 2, 0, 1),
    Sketcher.Constraint("Horizontal", 0), Sketcher.Constraint("Vertical", 1),
    Sketcher.Constraint("Horizontal", 2), Sketcher.Constraint("Vertical", 3),
    Sketcher.Constraint("Coincident", 0, 1, -1, 1),
    Sketcher.Constraint("Distance", 0, length),
    Sketcher.Constraint("Distance", 1, width),
]
sketch.addConstraint(constraints)
solver_status: int = sketch.solve()
App.ActiveDocument.recompute()
require(solver_status == 0, "Sketch solver failed")
require(bool(sketch.FullyConstrained), "Sketch retains degrees of freedom")
pad: Any = body.newObject("PartDesign::Pad", "MountPad")
pad.Profile = sketch
pad.Length = p["height"]
App.ActiveDocument.recompute()
check_shape(pad, length * width * p["height"])
if sketch.ViewObject is not None:
    sketch.ViewObject.Visibility = False
result = {"phase": "sketcher", "document": doc.Name, "fully_constrained": True,
          "volume_mm3": float(pad.Shape.Volume), "expected_volume_mm3": length * width * p["height"]}
'''

_CSG = '''
left: Any = doc.addObject("Part::Box", "OperandA")
right: Any = doc.addObject("Part::Box", "OperandB")
for operand in (left, right):
    operand.Length = p["length"]
    operand.Width = p["width"]
    operand.Height = p["height"]
right.Placement.Base = App.Vector(p["length"] - p["overlap"], 0, 0)
union: Any = doc.addObject("Part::Fuse", "Union")
difference: Any = doc.addObject("Part::Cut", "Difference")
intersection: Any = doc.addObject("Part::Common", "Intersection")
for operation in (union, difference, intersection):
    operation.Base = left
    operation.Tool = right
App.ActiveDocument.recompute()
section: float = p["width"] * p["height"]
check_shape(left, p["length"] * section)
check_shape(right, p["length"] * section)
check_shape(union, (2 * p["length"] - p["overlap"]) * section)
check_shape(difference, (p["length"] - p["overlap"]) * section)
check_shape(intersection, p["overlap"] * section)
for hidden in (left, right, difference, intersection):
    if hidden.ViewObject is not None:
        hidden.ViewObject.Visibility = False
result = {"phase": "csg", "document": doc.Name,
          "union_mm3": float(union.Shape.Volume), "difference_mm3": float(difference.Shape.Volume),
          "intersection_mm3": float(intersection.Shape.Volume)}
'''

_PARAMETRIC = '''
sheet: Any = doc.addObject("Spreadsheet::Sheet", "Dimensions")
aliases: tuple[tuple[str, str], ...] = (("length", "MountLength"), ("width", "MountWidth"), ("height", "MountHeight"))
for row, (key, alias) in enumerate(aliases, start=1):
    sheet.set("A" + str(row), key + " (mm)")
    sheet.set("B" + str(row), str(p[key]) + " mm")
    sheet.setAlias("B" + str(row), alias)
box: Any = doc.addObject("Part::Box", "ParametricMount")
box.setExpression("Length", "Dimensions.MountLength")
box.setExpression("Width", "Dimensions.MountWidth")
box.setExpression("Height", "Dimensions.MountHeight")
App.ActiveDocument.recompute()
initial_volume: float = p["length"] * p["width"] * p["height"]
check_shape(box, initial_volume)
require(math.isclose(float(box.Length.Value), p["length"], rel_tol=1e-9), "Length expression did not resolve")
require(math.isclose(float(box.Width.Value), p["width"], rel_tol=1e-9), "Width expression did not resolve")
require(math.isclose(float(box.Height.Value), p["height"], rel_tol=1e-9), "Height expression did not resolve")
# Prove that the dependency graph updates, then restore the requested dimensions.
sheet.set("B1", str(p["length"] * 0.9) + " mm")
App.ActiveDocument.recompute()
check_shape(box, initial_volume * 0.9)
sheet.set("B1", str(p["length"]) + " mm")
App.ActiveDocument.recompute()
check_shape(box, initial_volume)
result = {"phase": "parametric", "document": doc.Name,
          "volume_mm3": float(box.Shape.Volume), "expression_update_verified": True}
'''

_CAPSTONE = '''
mount: Any = doc.addObject("Part::Feature", "ProjectorMountBracket")
housing: Any = doc.addObject("Part::Feature", "SensorHousing")
length: float = p["plate_length"]
width: float = p["plate_width"]
thickness: float = p["plate_thickness"]
radius: float = p["fastener_diameter"] / 2
base: Any = Part.makeBox(length, width, thickness)
upright: Any = Part.makeBox(length, thickness, p["bracket_height"], App.Vector(0, width - thickness, thickness))
mount_shape: Any = base.fuse(upright)
hole_x: tuple[float, float] = ((length - p["mount_pitch_x"]) / 2, (length + p["mount_pitch_x"]) / 2)
hole_y: tuple[float, float] = ((width - p["mount_pitch_y"]) / 2, (width + p["mount_pitch_y"]) / 2)
for x in hole_x:
    for y in hole_y:
        mount_shape = mount_shape.cut(Part.makeCylinder(radius, thickness + 2, App.Vector(x, y, -1)))
    mount_shape = mount_shape.cut(Part.makeCylinder(radius, thickness + 2,
        App.Vector(x, width - thickness - 1, thickness + p["bracket_height"] / 2), App.Vector(0, 1, 0)))
mount.Shape = mount_shape.removeSplitter()
wall: float = p["wall"]
inner_length: float = p["sensor_length"] + 2 * p["clearance"]
inner_width: float = p["sensor_width"] + 2 * p["clearance"]
inner_height: float = p["sensor_height"] + p["clearance"]
outer_length: float = inner_length + 2 * wall
outer_width: float = inner_width + 2 * wall
outer_height: float = inner_height + wall
shell: Any = Part.makeBox(outer_length, outer_width, outer_height)
cavity: Any = Part.makeBox(inner_length, inner_width, inner_height + 1, App.Vector(wall, wall, wall))
shell = shell.cut(cavity)
# Front optical opening and rear cable opening; each cuts only one wall.
aperture_z: float = wall + inner_height / 2
epsilon: float = min(0.01, inner_width / 10, wall / 10)
lens: Any = Part.makeCylinder(p["lens_diameter"] / 2, wall + 2 * epsilon,
    App.Vector(outer_length / 2, -epsilon, aperture_z), App.Vector(0, 1, 0))
cable: Any = Part.makeCylinder(p["cable_diameter"] / 2, wall + 2 * epsilon,
    App.Vector(outer_length / 2, outer_width - wall - epsilon, aperture_z), App.Vector(0, 1, 0))
housing.Shape = shell.cut(lens).cut(cable).removeSplitter()
# Display the independent housing beside the bracket; this is not an assembly constraint.
housing.Placement.Base = App.Vector(length + 20, 0, 0)
App.ActiveDocument.recompute()
expected_mount: float = length * width * thickness + length * thickness * p["bracket_height"] - 6 * math.pi * radius ** 2 * thickness
expected_housing: float = outer_length * outer_width * outer_height - inner_length * inner_width * inner_height - math.pi * ((p["lens_diameter"] / 2) ** 2 + (p["cable_diameter"] / 2) ** 2) * wall
check_shape(mount, expected_mount)
check_shape(housing, expected_housing)
result = {"phase": "capstone", "document": doc.Name, "physical_fit_verified": False,
          "mount_volume_mm3": float(mount.Shape.Volume), "housing_volume_mm3": float(housing.Shape.Volume),
          "housing_inner_mm": [inner_length, inner_width, inner_height]}
'''


def build_script(phase: str, params: dict[str, object] | None = None) -> str:
    """Build a native script; does not connect, execute, or claim CAD success.

    Existing document names cause a deliberate error before a mutation. After a
    timeout, inspect the workstation; never turn an uncertain mutation into an
    automatic replay. Successful results are printed as one JSON object.
    """
    parameters = validate_parameters(phase, params)
    payload = json.dumps(parameters, sort_keys=True, separators=(",", ":"), allow_nan=False)
    preamble = dedent(f'''\
        # Generated by CortexCAD. Run only in FreeCAD's Python 3.11+ interpreter.
        from __future__ import annotations
        import json
        import math
        from typing import Any
        import FreeCAD as App
        import Part
        import Sketcher

        p: dict[str, float] = json.loads({payload!r})
        document_name: str = {("CortexCAD_" + phase.title())!r}
        if document_name in App.listDocuments():
            raise RuntimeError(document_name + " already exists; inspect, save and close it explicitly before another run")

        def require(condition: bool, message: str) -> None:
            if not condition:
                raise RuntimeError(message)

        def check_shape(feature: Any, expected_volume: float) -> None:
            shape: Any = feature.Shape
            require(not shape.isNull(), feature.Name + ": null shape")
            require(shape.isValid(), feature.Name + ": invalid shape")
            require(len(shape.Solids) == 1, feature.Name + ": expected one solid")
            require(math.isfinite(float(shape.Volume)) and shape.Volume > 0, feature.Name + ": nonpositive volume")
            require(math.isclose(float(shape.Volume), expected_volume, rel_tol=1e-7, abs_tol=1e-6), feature.Name + ": analytic volume mismatch")

        doc: Any = App.newDocument(document_name)
        App.setActiveDocument(doc.Name)
        result: dict[str, Any] = {{}}
        doc.openTransaction("CortexCAD " + {phase!r})
        try:
    ''')
    body = {"sketcher": _SKETCHER, "csg": _CSG, "parametric": _PARAMETRIC, "capstone": _CAPSTONE}[phase]
    # Keep the two success statements inside try while the exception handler is top-level.
    finish = "    App.ActiveDocument.recompute()\n    doc.commitTransaction()\nexcept Exception:\n    doc.abortTransaction()\n    App.ActiveDocument.recompute()\n    raise\nprint(json.dumps(result, sort_keys=True))\n"
    return preamble + indent(dedent(body).strip() + "\n", "    ") + finish
