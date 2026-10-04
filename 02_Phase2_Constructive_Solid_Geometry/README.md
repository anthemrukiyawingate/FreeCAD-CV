# Phase 2 — Boolean geometry with analytic checks

[CAPSTONE INTEGRATION TARGET] Bracket holes and a sensor cavity are material removal operations. This lesson makes intersections measurable before applying them to hardware.

Open `02_boolean_lab.ipynb`. Run offline first. The Build environment team owns branch `phase-2-csg`; DevOps accepts the connection before any live run.

Two equal boxes have dimensions `length × width × height`. Box A begins at the origin. Box B is translated in X by `length - overlap`; they share their Y and Z ranges. The schema adds `overlap` to the Phase 1 dimensions and requires `0 < overlap < length`, with every value in `[0.1, 2000] mm`.

Let `S = width × height`. Then:

| Result | Formula | Default (`40 × 30 × 12`, overlap `15`) |
| --- | --- | --- |
| Each operand | `length × S` | 14,400 mm³ |
| Intersection A ∩ B | `overlap × S` | 5,400 mm³ |
| Difference A − B | `(length − overlap) × S` | 9,000 mm³ |
| Union A ∪ B | `(2 × length − overlap) × S` | 23,400 mm³ |

The identity `V(union) + V(intersection) = V(A) + V(B)` catches mistakes in overlap interpretation. Difference is directional: for translated asymmetric operands, A − B and B − A are different shapes even when their volumes happen to match.

## Native acceptance

The live recipe creates `CortexCAD_Csg` with two `Part::Box` operands and linked `Part::Fuse`, `Part::Cut`, and `Part::Common` features. The native dependency graph retains the operands. A recompute precedes each shape inspection. All five shapes must be valid, contain exactly one solid and match their analytic volumes. Only Union is displayed initially to avoid ambiguous overlapping renderings; use the model tree's visibility controls to inspect each result individually.

After an accepted live run, use FreeCAD's Python console:

```python
import FreeCAD as App
doc = App.getDocument("CortexCAD_Csg")
App.setActiveDocument(doc.Name)
App.ActiveDocument.recompute()
for name in ("OperandA", "OperandB", "Union", "Difference", "Intersection"):
    feature = doc.getObject(name)
    print(name, feature.Shape.isValid(), len(feature.Shape.Solids), feature.Shape.Volume)
```

Save the document and record actual values, software versions and units in the QA evidence record. The notebook's analytic table and browser set diagram do not prove OpenCascade geometry. Native assertions remain unexecuted until a Windows or compatible FreeCAD run is recorded.

## Exercises

- Sweep overlaps 5, 15 and 35 mm. Predict the three result volumes before each run; save and explicitly close the previous lesson document before rebuilding.
- Prove that overlap zero and overlap equal to length are rejected locally. These are deliberate exclusions because the lesson demands a nonempty partial intersection and a nonempty difference.
- Explain why the 2D browser simulation represents this lesson only when both operands have equal constant depth.
- In a separate exercise design, replace the translated box with a cylindrical drill. State its axis and prove that the drill fully traverses the stock before checking a hole volume.

Continue to [Phase 3](../03_Phase3_Python_API_and_Spreadsheets/README.md).
