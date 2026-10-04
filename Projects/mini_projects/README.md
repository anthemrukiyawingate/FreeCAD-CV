# Mini projects — evidence before elaboration

Each exercise is a local curriculum extension. Ask the Build environment team to provision the appropriate phase branch. Retain the four notebook standards: top capstone callout, offline default, explicit types, and recompute before native inspection. These are assignments, not additional prevalidated FreeCAD models.

| Assignment | Start from | Parameter change or extension | Acceptance evidence |
| --- | --- | --- | --- |
| Cable spacer | Phase 1 | `length=30, width=18, height=4` | Fully constrained profile, one valid solid, volume 2,160 mm³ |
| Optical baffle blank | Phase 1 | `length=90, width=25, height=3` | Predicted volume 6,750 mm³; explain why this does not yet establish optical clearance |
| Overlap coupon | Phase 2 | `length=30, width=20, height=5, overlap=8` | Union 5,200; difference 2,200; intersection 800 mm³; all three native solids valid |
| Parametric standoff blank | Phase 3 | `length=16, width=16, height=12` | Final volume 3,072 mm³; temporary 90% update 2,764.8 mm³; restored expressions |
| Fastener coupon | Capstone derivation | A separate plate with a row of measured clearance hole diameters | Validate edge material; manufacture and measure hole sizes; record tool/material/process and chosen clearance |
| Connector access gauge | Capstone derivation | Measure the plug envelope and cable bend sweep, then construct a removable gauge | Gauge can be inserted and removed with real hardware installed; no claim from cable diameter alone |

For each project, write a prediction, create a falsifying test, implement, run local checks, then request an authorized native run. Include a failure case that would expose a stale recompute or a lost expression. Keep physical coupons and measurements traceable to a parameter file hash; avoid uploading personal device serial numbers to public source.

The fastener coupon and connector gauge deliberately require student design work. The core recipe makes a circular cable opening; a real USB/HDMI plug may need a larger rectangular access opening and strain relief. Treat that mismatch as a design requirement, not a reason to force an oversized plug through the example housing.
