# Phase 1 — constrain a profile, pad a mounting blank

[CAPSTONE INTEGRATION TARGET] The capstone bracket starts as a stable mounting profile. This lesson distinguishes coordinates that happen to look rectangular from constraints that keep the rectangle rectangular when dimensions change.

Open `01_constrained_mount.ipynb` in the CortexCAD Python 3.12+ kernel. Execute every cell in order with `CORTEXCAD_LIVE` unset. The default run validates inputs and generates the native script without opening a connection. The Build environment team owns the `phase-1-sketcher` branch; the DevOps team owns workstation connection and deployment acceptance.

## Learning sequence

1. Predict the free degrees of freedom. Four independent line segments begin with sixteen scalar coordinates.
2. Four endpoint coincidences remove eight degrees of freedom. Two horizontal and two vertical constraints remove four. Coincidence with the origin removes two. Driving length and width remove the last two. This count assumes independent constraints; the native solver supplies the actual acceptance result.
3. Build a `PartDesign::Body`, a `Sketcher::SketchObject`, the explicit constraints, and a `PartDesign::Pad`.
4. Recompute before checking `sketch.FullyConstrained`, solid validity and volume. Changing initial point coordinates alone is not equivalent to changing a driving constraint.

Parameters are `length`, `width`, `height` in millimetres, each finite, numeric and in `[0.1, 2000]`. Unknown keys, booleans and strings are rejected before IPC. Defaults are `60 × 40 × 6 mm`; the analytic volume is `length × width × height = 14,400 mm³`.

## Native acceptance

After DevOps has accepted the bridge, set `CORTEXCAD_LIVE=1` before starting the kernel, review the generated script, then run the submission cell once. The recipe creates `CortexCAD_Sketcher`; a document with that name already open causes a safe refusal. Save and close the existing document explicitly before a deliberate fresh run. An RPC timeout has an unknown outcome; inspect Windows before resubmitting.

Record the FreeCAD version, embedded Python version, request result and a saved `.FCStd` file outside source control. In FreeCAD's console, inspect:

```python
import FreeCAD as App
doc = App.getDocument("CortexCAD_Sketcher")
App.setActiveDocument(doc.Name)
App.ActiveDocument.recompute()
print(doc.MountProfile.FullyConstrained)  # must be True
print(doc.MountPad.Shape.isValid())      # must be True
print(len(doc.MountPad.Shape.Solids))    # must be 1
print(doc.MountPad.Shape.Volume)         # default 14400 mm³
```

The script requires solver status zero and a fully constrained sketch. It compares real OpenCascade volume with the formula using relative tolerance `1e-7` and absolute tolerance `1e-6 mm³`. A valid-looking screenshot alone is insufficient. Native checks remain pending until run in FreeCAD.

## Exercises

- Set width to 52 mm. Predict `18,720 mm³`, rebuild in a deliberately fresh document, and compare the native result.
- In a disposable saved copy, remove the width driving constraint. Recompute and demonstrate that `FullyConstrained` is false; restore it and check again. Never weaken the production assertion to make the exercise pass.
- Try `height=0`, `length=True` and an unknown key. Capture the local `ValueError` and demonstrate no request was sent.
- Explain why a pad needs a closed profile and why a redundant constraint can fail even if its image looks correct.

Continue to [Phase 2](../02_Phase2_Constructive_Solid_Geometry/README.md). API reference: [FreeCAD SketchObject](https://freecad.github.io/SourceDoc/d9/dad/classSketcher_1_1SketchObject.html) and [upstream Sketcher examples](https://github.com/FreeCAD/FreeCAD/blob/main/src/Mod/Sketcher/SketcherExample.py).
