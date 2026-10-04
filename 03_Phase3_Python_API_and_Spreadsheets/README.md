# Phase 3 — JSON, aliases, expressions and recompute

[CAPSTONE INTEGRATION TARGET] Device dimensions belong in a validated measurement contract. This lesson carries numeric JSON through a FreeCAD Spreadsheet dependency graph so a hardware change can regenerate geometry predictably.

Open `03_json_spreadsheet.ipynb`. It runs without a network by default. The Build environment team owns `phase-3-python-spreadsheets`; DevOps controls live workstation acceptance.

## Data flow

`JSON object → validate_parameters → numeric-only serialized payload → Spreadsheet cells → named expressions → recompute → native shape checks`

The accepted keys are `length`, `width`, and `height`, in millimetres; each is finite and within `[0.1, 2000]`. Unknown keys, booleans, strings, NaN and infinities fail before RPC. The notebook's strict JSON reader additionally rejects duplicate keys. A partial dictionary uses lesson defaults; a production measurement record must be complete and reviewed.

| Cell | Alias | Units | Driven property |
| --- | --- | --- | --- |
| B1 | MountLength | mm | `ParametricMount.Length` |
| B2 | MountWidth | mm | `ParametricMount.Width` |
| B3 | MountHeight | mm | `ParametricMount.Height` |

The live recipe creates `CortexCAD_Parametric`. The expressions are `Dimensions.MountLength`, `Dimensions.MountWidth`, and `Dimensions.MountHeight`. Values are stored as quantities such as `60.0 mm`; arithmetic therefore preserves length units.

## Native acceptance

The recipe first checks that the expression-resolved dimensions and volume match the input. It then changes B1 to 90% of the input length, recomputes and checks for 90% of the original volume. Finally it restores B1, recomputes, verifies the original volume, and commits one transaction. Default final dimensions are `60 × 40 × 6 mm`, final volume `14,400 mm³`; the temporary update should produce `12,960 mm³`.

```python
import FreeCAD as App
doc = App.getDocument("CortexCAD_Parametric")
App.setActiveDocument(doc.Name)
App.ActiveDocument.recompute()
print(doc.ParametricMount.ExpressionEngine)
print(doc.ParametricMount.Length, doc.ParametricMount.Width, doc.ParametricMount.Height)
print(doc.ParametricMount.Shape.Volume)
```

Archive the FreeCAD document and response alongside the measurement revision. A timeout means outcome unknown, including the possibility that a temporary update or final commit completed remotely. Inspect the document before rerunning. Duplicate document names intentionally block blind retries.

## Exercises

- Submit `{"length": 80, "width": 50, "height": 8}`; predict `32,000 mm³`, an intermediate `28,800 mm³`, and the restored result.
- Try a duplicate `length` key, a string containing Python, and JSON containing `NaN`. Explain which layer rejects each payload.
- In a disposable copy, remove the Height expression, change B3 and recompute. Demonstrate why a dimension assertion is needed in addition to a successful network response.
- Propose a measurement revision format that tracks units, instrument, uncertainty, reviewer and actual hardware identity separately from executable dimensions. Never concatenate a measured label into Python source.

Continue to the [capstone](../Projects/CAPSTONE_Plato_Shadows_Hardware_Mounts/README.md). FreeCAD references: [Spreadsheet API](https://freecad.github.io/SourceDoc/d0/da8/classSpreadsheet_1_1Sheet.html) and [Python alias binding](https://freecad.github.io/API/d3/d33/classSpreadsheet_1_1SheetPy.html).
