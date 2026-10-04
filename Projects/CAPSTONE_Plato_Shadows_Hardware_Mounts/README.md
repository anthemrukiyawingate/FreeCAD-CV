# Plato Shadows — measured hardware integration

[CAPSTONE INTEGRATION TARGET] Combine constrained stock, Boolean removal and validated parameter data into a projector mounting bracket and sensor housing candidate, then qualify the real installation.

The Plato Shadows concept is an original idea by **Tee Ken Ng, [@TeeKenNG on TikTok](https://www.tiktok.com/@teekenng)**. This repository is an independent curriculum implementation; attribution does not imply endorsement.

**Current basis: example dimensions only.** No projector, webcam, device mounting drawing, load case or physical fit measurements were supplied. The provided model is a reproducible fixture exercise. It does not establish exact compatibility, structural suitability, manufacturability or the completed projector/webcam installation.

Open `04_hardware_integration.ipynb`; run offline first. The Build environment team owns `phase-4-capstone` and the GitHub transition. DevOps owns live workstation access, installation qualification and deployment. This package hands off source and explicit acceptance gates to those teams.

## What the recipe constructs

The projector candidate is an L bracket: a rectangular horizontal plate, a full-width rear upright, four plate holes in a centered rectangular pattern and two upright holes. The six through holes share one diameter. Upright holes use the same X pitch and lie halfway up the upright. The script joins the stock, cuts each hole, removes internal splitters, recomputes and checks for one valid solid.

The sensor candidate is a rectangular open-top shell with one centered front optical opening and one centered rear cable opening. Side clearance is applied on both sides of X and Y; top allowance is applied once in Z. A solid floor supports the device. The housing is displayed 20 mm beyond the bracket in X for inspection; this is a display arrangement, not an assembled mechanical interface.

The base recipe has no lid, positive sensor retention, housing-to-bracket attachment, cable strain relief, counterbores, threaded inserts, gussets or leveling mechanism. Add those features only after measurement and test revision. Devices with offset optics, nonrectangular mounting patterns, different fasteners, ventilation cutouts or large plug envelopes require a geometry extension. Record each mismatch explicitly at gate M1 instead of treating the generic fixture as an exact mount.

## Strict dimension contract

`measurement.example.json` is the complete **teaching fixture**, not a manufacturer specification. Copy its keys into a reviewed measurement file outside the distributed example. Set `CORTEXCAD_MEASUREMENTS` to that file's absolute path before opening the notebook. The notebook rejects incomplete records, duplicate keys, unknown keys, strings, booleans and nonfinite values. `measurement.schema.json` specifies JSON shape and scalar ranges; `validate_parameters("capstone", record)` additionally enforces cross-field geometry rules.

All values are millimetres. Each has minimum 0.1; maximum is 2000 unless a stricter limit is listed. Metadata belongs in a separate acceptance record; do not add comments, units strings, labels or new keys to the numeric payload.

| Key | Example | Measurement or design meaning |
| --- | ---: | --- |
| plate_length | 160 | Horizontal plate X extent |
| plate_width | 100 | Horizontal plate Y extent |
| plate_thickness | 6 | Plate thickness and upright thickness |
| mount_pitch_x | 100 | Hole center-to-center pitch in X for both plate and upright |
| mount_pitch_y | 60 | Plate hole center-to-center pitch in Y |
| fastener_diameter | 5.5 | Finished clearance-hole diameter, not nominal thread size |
| edge_margin | 10 | Minimum reserved edge material used by layout checks |
| bracket_height | 40 | Upright height above the plate top |
| sensor_length | 40 | Device body envelope along housing X |
| sensor_width | 30 | Device body envelope along housing Y |
| sensor_height | 25 | Device height above the floor |
| clearance | 0.6 | Per-side X/Y allowance and one top allowance; maximum 10 |
| wall | 3 | Housing side and floor thickness; maximum 20 |
| cable_diameter | 8 | Circular rear access opening; verify actual connector envelope separately |
| lens_diameter | 12 | Circular front optical opening; verify field-of-view clearance separately |

The rectangular base pattern is centered at `(plate_length/2, plate_width/2)`. Center positions are `x = (plate_length ± mount_pitch_x)/2`, `y = (plate_width ± mount_pitch_y)/2`. The upright occupies the rearmost `plate_thickness` of Y.

The validator requires both pitches to exceed hole diameter; `edge_margin ≥ max(plate_thickness, fastener_diameter)`; `mount_pitch_x + fastener_diameter + 2×edge_margin ≤ plate_length`; `mount_pitch_y + fastener_diameter + 2×(edge_margin + plate_thickness) ≤ plate_width`; and `bracket_height ≥ fastener_diameter + 2×edge_margin`. These conservative layout rules reserve space around the upright and holes. They are geometric checks, not stress allowables.

Housing cavity dimensions are `iL = sensor_length + 2×clearance`, `iW = sensor_width + 2×clearance`, `iH = sensor_height + clearance`. Outer dimensions are `oL=iL+2×wall`, `oW=iW+2×wall`, `oH=iH+wall`. The larger aperture diameter plus `2×wall` must fit both `iL` and `iH`. Housing outer dimensions may not exceed 2000 mm. Optical and cable openings are centered at `x=oL/2`, `z=wall+iH/2`; measure the real locations before accepting this assumption.

## Analytic and native checks

With hole radius `r = fastener_diameter/2`, thickness `t`, upright height `b`, plate length `L` and width `W`:

`V_mount = L×W×t + L×t×b − 6×π×r²×t`.

With front/rear aperture radii `r_lens`, `r_cable`:

`V_housing = oL×oW×oH − iL×iW×iH − π×(r_lens²+r_cable²)×wall`.

These formulas depend on disjoint holes traversing only their intended stock and apertures remaining inside the wall face. The recipe's relation checks maintain those assumptions. Both final shapes must be non-null, valid, positive-volume single solids. The native script compares real volumes with the formulas using relative tolerance `1e-7` and absolute tolerance `1e-6 mm³`; it reports `physical_fit_verified: false` regardless of CAD success.

```python
import FreeCAD as App
doc = App.getDocument("CortexCAD_Capstone")
App.setActiveDocument(doc.Name)
App.ActiveDocument.recompute()
for name in ("ProjectorMountBracket", "SensorHousing"):
    obj = doc.getObject(name)
    print(name, obj.Shape.isValid(), len(obj.Shape.Solids), obj.Shape.Volume)
```

For parameter changes, save and explicitly close the previous lesson document before a deliberate fresh run. Existing document names cause a refusal before mutation. A timed-out request is not evidence of rollback; inspect Windows before retrying. Export only the intended final solids after recompute and native inspection, using FreeCAD's UI and the accepted manufacturing format.

## Measured-hardware acceptance gates

All gates start **pending**. Use `ACCEPTANCE_RECORD.md` as the record, copying it to the team's evidence location. A failed or unknown gate blocks a fit or deployment claim.

| Gate | Required evidence | Pass condition and owner |
| --- | --- | --- |
| M0 — measurement provenance | Hardware model/revision; dimensioned photographs/drawings; instrument and resolution; repeated measurements and uncertainty; mm convention; measurement-file hash and reviewer | Every required dimension has a traceable basis; physical owner and mechanical reviewer accept it |
| M1 — recipe applicability | Real hole pattern/axes, thread engagement depth, screw and washer head envelopes, sensor body/PCB/lens/cable offsets, vents and keep-out regions | Every recipe assumption matches hardware, or a tested geometry extension resolves it; mechanical reviewer accepts |
| M2 — native CAD | Exact FreeCAD/Python/bridge versions; final parameter hash; solver/shape/volume results; saved `.FCStd`; separately exported accepted solids; visual sections and interference review | Native assertions pass; no lost expressions or unexpected extra solids; CAD reviewer accepts |
| M3 — process and fit coupon | Material, manufacturing process/orientation, dimensional compensation, fastener coupon, measured finished holes/walls/clearances, roughness and insert installation checks | Coupon and prototype clearances match the approved tolerance stack; fabrication owner accepts |
| M4 — retention and loading | Actual device masses/center of gravity; bracket orientation; cantilever and torque assumptions; anchors/substrate; screw engagement; positive sensor retention; housing attachment; agreed load test and inspection | Mechanical owner approves the design and test plan, and physical test evidence meets that plan; unloaded CAD volume is insufficient |
| M5 — optical, electrical and service access | Projector throw/offset/focus/keystone and full image cone; webcam field of view; lens clearance through its full angle; cable plug insertion and bend sweep; strain relief; ventilation and heat; access for fastener tools | Assembled hardware meets the measured optical and access envelope with no clipping, blocked vents, forced connectors or loose sensor; integration owner accepts |
| M6 — repeatable installation | Projector/webcam pose and calibration revision; alignment target; measured mapping error and agreed threshold; remount/restart repeatability; sustained-run observation; removal/recovery procedure | DevOps and integration owner accept measured results and sign the deployment record |

The mounting load test, allowable deflection, thermal duration and calibration thresholds must be agreed from the real equipment and installation context. The example does not invent values. Do not infer a capacity from a wall thickness or grant physical acceptance from a visually plausible render.

## Tolerance and measurement procedure

1. Define a coordinate frame on each device. Measure the largest body envelope, protrusions, lens center, connector positions, mounting pattern, surface flatness and access clearances. Record axes and datums on the drawing.
2. Measure mating features repeatedly. Separate nominal fastener size from clearance-hole diameter and from head/washer clearance. Check depth limits so a screw cannot bottom out or enter a device's internals.
3. Build a tolerance stack using measurement uncertainty, material/process variation, surface finish and required assembly allowance. The example clearance of 0.6 mm is not a universal printer setting.
4. Make a cheap hole and connector coupon before a full assembly. Measure the manufactured result rather than assuming slicer dimensions equal physical dimensions.
5. Trial fit with power off and with the actual connector attached. Verify insertion/removal paths, cable bend radius, retention and tool access. Evaluate optical and thermal requirements during the approved integration test.
6. Revise the numeric record and design together. Keep the previous accepted CAD file, test evidence, measurement hash and process settings so a change is reproducible.

## Handover deliverables

Provide source, generated-script hash, complete dimensions, CAD evidence, prototype measurements, design deviations and signed gate results to Build environment and DevOps. Build environment performs commits, branches and GitHub handover; DevOps performs deployment, live validation and any publication. At initial delivery, this directory establishes the model and acceptance procedure; M0–M6 require external hardware and team evidence.
