# Curriculum implementation and falsification evidence

Task packet: Senior AI Developer and QA Auditor executing S1-CAD, S2-CSG, S3-PARAM and S4-HARDWARE. Evidence below is from actual local runs on 2026-10-03; native geometry assertions have not been executed because the task has no FreeCAD workstation or measured hardware.

## Interfaces and packaging

`cortexcad.recipes.build_script(phase: str, params: dict[str, object] | None = None) -> str` accepts `sketcher`, `csg`, `parametric`, or `capstone`. `validate_parameters` returns a fresh normalized `dict[str, float]`; `DEFAULTS` and `PHASES` describe the public lesson contract. Standard-library-only source generation works in the installed package. Generated scripts parse as Python 3.11; notebook kernels require Python 3.12+.

Generation is deterministic. User values are constrained numeric data embedded through JSON, not interpolated labels or Python fragments. Unknown keys, non-object inputs, booleans, text, nonfinite values, excessive sizes, overlapping mounting holes and invalid clearances fail before IPC. Native document names are deterministic. Replaying an existing name raises before any document mutation; failed transactions abort and recompute. Native scripts never close or replace an existing document.

Notebook package imports work from arbitrary current directories when CortexCAD is installed. A source checkout can instead be located through `CORTEXCAD_ROOT` or a current-directory ancestor. The capstone's explicit measurement path is absolute-resolved; there is no assumed working directory. Every first cell starts with `[CAPSTONE INTEGRATION TARGET]`. Every live submission uses the explicit `CORTEXCAD_LIVE=1` gate and `FreeCADClient.run_recipe`; default cells only generate and inspect source and arithmetic.

## Actual test-first sequence

1. Created `tests/test_recipes.py` with fourteen contract test methods before implementing `cortexcad/recipes.py`.
2. Ran `python3 -m unittest discover -s tests -p test_recipes.py -v`: exit 1, `ModuleNotFoundError: No module named 'cortexcad.recipes'`. This was the observed first red run, not a retrospectively inferred failure.
3. Implemented bounded validation, four native script templates, transactional error handling and the example capstone record. Re-ran the same command: fourteen tests passed.
4. Added a new falsifying test for mounting holes closer than their diameter. Ran it before the fix: exit 1, two failing subcases (`mount_pitch_x`, `mount_pitch_y`), `AssertionError: ValueError not raised`.
5. Added the cross-hole spacing rule. Re-ran: fifteen tests passed. Reviewed aperture cutters and limited their overrun relative to cavity width so an unusually shallow housing does not accidentally drill its opposite wall.
6. Added a notebook test requiring all four named lessons to execute offline from an unrelated temporary current directory, with live `run_recipe` patched to fail. Ran before creating notebooks: exit 1, `FileNotFoundError` for `01_constrained_mount.ipynb`.
7. Created four instructional notebooks with clean outputs. Re-ran: sixteen tests passed, including every code cell in all four notebooks under the offline contract.

Local interpreter at these runs: Python 3.14.8 on Linux. The Python 3.11 syntax check uses `ast.parse(..., feature_version=(3, 11))`; it is a syntax check, not an execution of FreeCAD's embedded interpreter. Root QA records any additional Python 3.12/3.11 test environments.

## Falsification coverage

| Claim | Falsifying test/evidence | Boundary |
| --- | --- | --- |
| Parameters cannot inject executable text | Unknown-key/text/bool/nonfinite/big-integer cases fail; deterministic JSON round-trip | Local real Python validation |
| Unsupported geometry is rejected | CSG degeneracy, plate edge/upright collision, hole overlap and housing aperture cases | Numeric geometry contract only |
| Retry does not overwrite a lesson | Generated script executed with an existing-document API double; no mutation observed | Control-flow double, not FreeCAD |
| Transaction failure triggers cleanup | First object insertion raises; observed sequence is open, abort, recompute | Control-flow double, not remote cancellation |
| Notebook previews do not call the workstation | All cells executed with `CORTEXCAD_LIVE=0`, unrelated cwd and live method forced to raise | Offline Python execution |
| Sketch is constrained and pad is valid | Native script requires solver status zero, FullyConstrained, one valid solid and analytic volume | Real FreeCAD gate still pending |
| Boolean output matches analytic geometry | Native checks of two operands plus fuse/cut/common | Real FreeCAD gate still pending |
| Spreadsheet edits propagate | Native dimension checks, 90% update, recompute, volume check, restore, recompute | Real FreeCAD gate still pending |
| Bracket and housing fit hardware | M0–M6 measured acceptance gates | Pending actual hardware, process and integration evidence |

The small FreeCAD API doubles only reach replay refusal and failure cleanup. They do not fabricate successful geometry, solver values or solid validity. Offline arithmetic is explicitly distinct from the native assertions and physical acceptance.

## Native run protocol for DevOps

Run each phase once against the approved Windows endpoint after recording exact FreeCAD, embedded Python and bridge versions. Review the complete generated script. Confirm the response and the native model, then save `.FCStd` evidence and record all asserted values. Exercise a deliberately invalid local payload and a deliberate duplicate-document request; the former must send no IPC and the latter must leave the existing document intact. A mutation timeout remains unknown even if transaction abort is implemented: abort runs only if the remote Python execution reaches its exception handler. Inspect the workstation before retrying.

Build environment owns source control, phase branch creation and GitHub transition. DevOps owns deployment and native runtime acceptance. Source delivery makes no public release, measured fit or live performance claim.

FreeCAD API references used during implementation: [SketchObject and FullyConstrained](https://freecad.github.io/SourceDoc/d9/dad/classSketcher_1_1SketchObject.html), [upstream Sketcher example](https://github.com/FreeCAD/FreeCAD/blob/main/src/Mod/Sketcher/SketcherExample.py), [Spreadsheet Sheet](https://freecad.github.io/SourceDoc/d0/da8/classSpreadsheet_1_1Sheet.html), and [Spreadsheet Python aliases](https://freecad.github.io/API/d3/d33/classSpreadsheet_1_1SheetPy.html). Source references inform implementation; they do not substitute for running the targeted FreeCAD version.
