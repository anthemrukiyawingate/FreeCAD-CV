# Sprint backlog and phase execution structure

Story points are relative estimates, not elapsed-time promises. Every task below specifies inputs, owned outputs, a falsifying test, dependencies and a measurable acceptance condition. Source implementation and deployment acceptance are tracked separately. Build exclusively owns version control; DevOps exclusively owns deployment.

## Definition of ready and done

Ready: inputs are present, interfaces agreed, output ownership isolated, and the smallest falsifying test is stated. Done: the test fails before implementation, then passes with the implementation; interfaces and failure modes are documented; packaging is reviewable; the QA report names any unverified environment. An external gate remains pending until its owner supplies evidence.

Use `python scripts/task_harness.py TASK-ID` to emit a complete deployment packet. The harness prints work instructions and never launches an AI client, changes Git, or touches a workstation. Actual independent source agents were dispatched for IPC/MCP, curriculum/native recipes, and graphics; see AGENT_PROTOCOL.md.

## Sprint 0 — Infrastructure bootstrapping

Estimated effort: 33 points. Phase branch: main / infrastructure. Branch creation is a Build team action.

### S0-README — README.md

- **Owner / estimate:** Architecture / 2 points.
- **Dependencies:** None; initial brief.
- **Inputs:** User brief and ownership policy.
- **Outputs:** README.md, LICENSE, repository structure.
- **Test first / falsification:** Missing attribution or mixed MCP/XML-RPC instructions fails review.
- **Acceptance:** All five required README sections present; Build/DevOps boundaries explicit.
- **Status:** implemented; see QA_REPORT for evidence.

### S0-ENV — pyproject.toml

- **Owner / estimate:** Development / Build / 3 points.
- **Dependencies:** S0-README.
- **Inputs:** Python 3.12+ host and package index.
- **Outputs:** pyproject.toml, isolated venv, dependency lock and CI.
- **Test first / falsification:** Unsupported Python or missing optional SDK cannot pass integration.
- **Acceptance:** Install in clean environment, run checks and build wheel.
- **Status:** implemented; see QA_REPORT for evidence.

### S0-IPC — Typed client

- **Owner / estimate:** IPC agent / 8 points.
- **Dependencies:** S0-ENV.
- **Inputs:** Reference execute_code/ping contract and loopback fake server.
- **Outputs:** Typed client, timeout transport, redacted logs, IPC_INTERFACE.md.
- **Test first / falsification:** Disconnect after write must not replay a mutation; malformed success rejected.
- **Acceptance:** Client falsification tests pass; exact True ping and explicit statuses.
- **Status:** implemented; see QA_REPORT for evidence.

### S0-MCP — Stdio server

- **Owner / estimate:** IPC agent / 5 points.
- **Dependencies:** S0-IPC.
- **Inputs:** Python MCP SDK and bounded recipe interface.
- **Outputs:** Stdio server, registration instructions and SDK tests.
- **Test first / falsification:** Raw Python tool absent; false/NaN dimensions rejected before IPC.
- **Acceptance:** SDK discovers bounded tools and offline preview through real stdio session.
- **Status:** implemented; see QA_REPORT for evidence.

### S0-QA — Notebook/static validation

- **Owner / estimate:** QA / Build / 3 points.
- **Dependencies:** S0-ENV.
- **Inputs:** Notebook and HTML artifact contracts.
- **Outputs:** Notebook/static validation, test-first evidence, CI checks.
- **Test first / falsification:** Saved notebook output, syntax error, missing link and leaked .env fail.
- **Acceptance:** Automated local checks green; CI configuration supplied for Build.
- **Status:** implemented; see QA_REPORT for evidence.

### S0-HANDOFF — DEVOPS_HANDOFF.md

- **Owner / estimate:** Architecture / DevOps / 5 points.
- **Dependencies:** S0-IPC.
- **Inputs:** Cross-platform topology and ownership.
- **Outputs:** DEVOPS_HANDOFF.md, BUILD_HANDOFF.md, release checklist.
- **Test first / falsification:** Timeout never documented as cancellation; no manufactured endpoint or SHA.
- **Acceptance:** Network, hardware, calibration, recovery and rollout steps reviewable.
- **Status:** implemented; see QA_REPORT for evidence.

### S0-IMPORT — Managed GitHub repository

- **Owner / estimate:** Build environment / 2 points.
- **Dependencies:** S0-QA, S0-HANDOFF.
- **Inputs:** Reviewed source archive and checksum.
- **Outputs:** Managed GitHub repository, phase branches and revision.
- **Test first / falsification:** Checksum mismatch or missing source blocks import.
- **Acceptance:** Build verifies archive and records source revision.
- **Status:** pending external team gate.

### S0-WINDOWS — Version inventory

- **Owner / estimate:** DevOps / 5 points.
- **Dependencies:** S0-IPC, S0-HANDOFF.
- **Inputs:** Windows host, approved account, FreeCAD/addon and SSH route.
- **Outputs:** Version inventory, live doctor output, allow-list evidence.
- **Test first / falsification:** Closed tunnel/disallowed source rejected within documented bound.
- **Acceptance:** Windows GUI connected through approved route; real recovery demonstrated.
- **Status:** pending external team gate.

## Sprint 1 — Sketcher & PartDesign

Estimated effort: 16 points. Phase branch: phase-1-sketcher. Branch creation is a Build team action.

### S1-CAD — Constrained sketch and PartDesign pad recipe

- **Owner / estimate:** Curriculum agent / 5 points.
- **Dependencies:** S0-IPC.
- **Inputs:** Positive length/width/height in millimeters.
- **Outputs:** Constrained sketch and PartDesign pad recipe.
- **Test first / falsification:** Invalid dimensions rejected; duplicate document preserved; solver failure aborts.
- **Acceptance:** Native script asserts zero DOF, valid solid and length×width×height volume.
- **Status:** implemented; see QA_REPORT for evidence.

### S1-LESSON — Phase 1 notebook

- **Owner / estimate:** Curriculum agent / 3 points.
- **Dependencies:** S1-CAD.
- **Inputs:** Recipe and capstone mounting-face rationale.
- **Outputs:** Phase 1 notebook, guide and exercises.
- **Test first / falsification:** First cell missing CAPSTONE target or live execution by default fails.
- **Acceptance:** Offline notebook runs cleanly; learner predicts DOF and checks a pad.
- **Status:** implemented; see QA_REPORT for evidence.

### S1-DEMO — Standalone constraint engine mock and landing workbench

- **Owner / estimate:** Graphics agent / 5 points.
- **Dependencies:** S1-CAD.
- **Inputs:** Four-parameter axis-aligned rectangle model.
- **Outputs:** Standalone constraint engine mock and landing workbench.
- **Test first / falsification:** Redundant lock must not reduce DOF twice; locked motion projected out.
- **Acceptance:** Math tests pass; keyboard controls and independent DOF visible.
- **Status:** implemented; see QA_REPORT for evidence.

### S1-LIVE — Solver screenshot

- **Owner / estimate:** DevOps / QA / 3 points.
- **Dependencies:** S0-WINDOWS, S1-LESSON.
- **Inputs:** Live FreeCAD with clean course document namespace.
- **Outputs:** Solver screenshot, pad volume and replay-guard evidence.
- **Test first / falsification:** Existing course document rejected without destructive overwrite.
- **Acceptance:** Actual FreeCAD solver/solid measurements match the notebook.
- **Status:** pending external team gate.

## Sprint 2 — Constructive Solid Geometry

Estimated effort: 16 points. Phase branch: phase-2-csg. Branch creation is a Build team action.

### S2-CSG — Union/cut/common recipes and native analytic checks

- **Owner / estimate:** Curriculum agent / 5 points.
- **Dependencies:** S1-CAD.
- **Inputs:** Two aligned boxes with bounded overlap.
- **Outputs:** Union/cut/common recipes and native analytic checks.
- **Test first / falsification:** Zero/oversized overlap and null/invalid result fail before acceptance.
- **Acceptance:** Volumes satisfy common+cut=A and union+common=A+B.
- **Status:** implemented; see QA_REPORT for evidence.

### S2-LESSON — Phase 2 notebook

- **Owner / estimate:** Curriculum agent / 3 points.
- **Dependencies:** S2-CSG.
- **Inputs:** Set-operation vocabulary and dimensions.
- **Outputs:** Phase 2 notebook, mini-project and guide.
- **Test first / falsification:** Visible overlap alone cannot serve as proof of volume identities.
- **Acceptance:** Offline lesson runs; learner predicts and verifies three operations.
- **Status:** implemented; see QA_REPORT for evidence.

### S2-DEMO — Union/difference/intersection engine mock

- **Owner / estimate:** Graphics agent / 5 points.
- **Dependencies:** S1-DEMO, S2-CSG.
- **Inputs:** 2D membership/area equations.
- **Outputs:** Union/difference/intersection engine mock.
- **Test first / falsification:** Disjoint, tangent, containment and identical shapes tested.
- **Acceptance:** Drawn operation and analytic area agree; operations accessible by keyboard.
- **Status:** implemented; see QA_REPORT for evidence.

### S2-LIVE — Real CAD valid-solid counts and volume results

- **Owner / estimate:** DevOps / QA / 3 points.
- **Dependencies:** S1-LIVE, S2-LESSON.
- **Inputs:** Native Boolean operation scripts and expected values.
- **Outputs:** Real CAD valid-solid counts and volume results.
- **Test first / falsification:** Solver/boolean invalidity blocks phase completion.
- **Acceptance:** All three operations pass native assertions on Windows.
- **Status:** pending external team gate.

## Sprint 3 — Python API & Spreadsheets

Estimated effort: 16 points. Phase branch: phase-3-python-spreadsheets. Branch creation is a Build team action.

### S3-PARAM — Spreadsheet aliases

- **Owner / estimate:** Curriculum agent / 5 points.
- **Dependencies:** S2-CSG.
- **Inputs:** Strict finite JSON dimension schema.
- **Outputs:** Spreadsheet aliases, expression links and recompute recipe.
- **Test first / falsification:** Unknown keys, booleans, nonfinite values and injected text rejected.
- **Acceptance:** Change/restore a cell and assert recomputed bounds/volume.
- **Status:** implemented; see QA_REPORT for evidence.

### S3-LESSON — Phase 3 notebook and parameter exercises

- **Owner / estimate:** Curriculum agent / 3 points.
- **Dependencies:** S3-PARAM.
- **Inputs:** Validated JSON and expression dependency graph.
- **Outputs:** Phase 3 notebook and parameter exercises.
- **Test first / falsification:** Stale cached dimensions cannot be reported as fresh geometry.
- **Acceptance:** Offline lesson runs; learner explains JSON→cell→expression→recompute.
- **Status:** implemented; see QA_REPORT for evidence.

### S3-DEMO — Live sliders

- **Owner / estimate:** Graphics agent / 5 points.
- **Dependencies:** S2-DEMO, S3-PARAM.
- **Inputs:** Dimensional product and parameter transitions.
- **Outputs:** Live sliders, target/current values and interpolated geometry.
- **Test first / falsification:** Volume stale after slider change or frame-rate-dependent lerp fails.
- **Acceptance:** Math tests validate volume and interpolation; reset restores state.
- **Status:** implemented; see QA_REPORT for evidence.

### S3-LIVE — Before/after dimensions and expression-link evidence

- **Owner / estimate:** DevOps / QA / 3 points.
- **Dependencies:** S2-LIVE, S3-LESSON.
- **Inputs:** Actual spreadsheet-driven FreeCAD document.
- **Outputs:** Before/after dimensions and expression-link evidence.
- **Test first / falsification:** UI label changes without shape change fail acceptance.
- **Acceptance:** Spreadsheet edit updates physical solid after explicit recompute.
- **Status:** pending external team gate.

## Sprint 4 — Plato Shadows hardware and release

Estimated effort: 53 points. Phase branch: phase-4-capstone. Branch creation is a Build team action.

### S4-HARDWARE — Parametric mount/bracket and sensor housing

- **Owner / estimate:** Curriculum agent / 8 points.
- **Dependencies:** S1-CAD, S2-CSG, S3-PARAM.
- **Inputs:** Teaching fixture and hardware measurement contract.
- **Outputs:** Parametric mount/bracket and sensor housing, notebook.
- **Test first / falsification:** Overlapping holes, thin walls and cavity collisions rejected.
- **Acceptance:** Typed validated scripts include native shape and dimension checks.
- **Status:** implemented; see QA_REPORT for evidence.

### S4-MEASURE — Measured drawing

- **Owner / estimate:** Hardware integrator / DevOps / 5 points.
- **Dependencies:** S0-HANDOFF.
- **Inputs:** Actual projector, camera, cables, datum and mounting surface.
- **Outputs:** Measured drawing, model IDs, uncertainty, supported parameter payload.
- **Test first / falsification:** Unmeasured example values cannot be labeled exact fit.
- **Acceptance:** Measurement table complete; schema can represent chosen hardware.
- **Status:** pending external team gate.

### S4-ADAPT — Additional tested hole/retention/optical geometry when required

- **Owner / estimate:** Development / hardware integrator / 8 points.
- **Dependencies:** S4-MEASURE, S4-HARDWARE.
- **Inputs:** Measured hardware outside supported recipe family, if any.
- **Outputs:** Additional tested hole/retention/optical geometry when required.
- **Test first / falsification:** Forcing incompatible hole pattern into current scalar payload rejected.
- **Acceptance:** Extend schema/test/recipe together or record adaptation not required.
- **Status:** pending external team gate.

### S4-DEMO — Capstone layout engine mock

- **Owner / estimate:** Graphics agent / 5 points.
- **Dependencies:** S3-DEMO, S4-HARDWARE.
- **Inputs:** Example dimensions and projected layout math.
- **Outputs:** Capstone layout engine mock, clearance readout and disclaimer.
- **Test first / falsification:** Negative cavity clearance cannot show fit success.
- **Acceptance:** Mock explains layout while clearly identifying teaching fixture.
- **Status:** implemented; see QA_REPORT for evidence.

### S4-FIT — Native CAD acceptance

- **Owner / estimate:** Hardware integrator / DevOps / 8 points.
- **Dependencies:** S3-LIVE, S4-MEASURE, S4-ADAPT.
- **Inputs:** Measured recipe, fabrication method and load assumptions.
- **Outputs:** Native CAD acceptance, physical coupon and installed fit report.
- **Test first / falsification:** Interference, insufficient engagement, blocked optics/airflow fail.
- **Acceptance:** Hardware engineer signs fit/retention and records actual deviations.
- **Status:** pending external team gate.

### S4-CALIBRATE — Device modes

- **Owner / estimate:** DevOps / application integrator / 8 points.
- **Dependencies:** S4-FIT.
- **Inputs:** Installed hardware and the projection/capture consumer application.
- **Outputs:** Device modes, calibration transforms, residual and latency report.
- **Test first / falsification:** Changed camera mode or shifted bracket invalidates prior mapping.
- **Acceptance:** Held-out marker errors and latency meet predeclared application thresholds.
- **Status:** pending external team gate.

### S4-PERF — 30-second interaction metrics and accessibility checks

- **Owner / estimate:** QA / DevOps / 5 points.
- **Dependencies:** S1-DEMO, S2-DEMO, S3-DEMO, S4-DEMO.
- **Inputs:** Target display/GPU/browser and 4K viewport.
- **Outputs:** 30-second interaction metrics and accessibility checks.
- **Test first / falsification:** Unmeasured 60 FPS claim, overflow or reduced-motion failure rejected.
- **Acceptance:** Record FPS/frame percentiles/DRS; qualify hardware-specific results.
- **Status:** pending external team gate.

### S4-PAGES — Public Pages URL and all phase navigation checks

- **Owner / estimate:** DevOps / 3 points.
- **Dependencies:** S0-IMPORT, S4-PERF.
- **Inputs:** Build-provided accepted branch containing /docs.
- **Outputs:** Public Pages URL and all phase navigation checks.
- **Test first / falsification:** Switching local Git branch alone cannot change Pages source.
- **Acceptance:** Set explicit branch/docs source; verify deployment and rollback.
- **Status:** pending external team gate.

### S4-RELEASE — Accepted versioned curriculum release and operational ownership

- **Owner / estimate:** Build / DevOps / QA / 3 points.
- **Dependencies:** S4-FIT, S4-CALIBRATE, S4-PAGES.
- **Inputs:** Checksums, QA results and all deployment sign-offs.
- **Outputs:** Accepted versioned curriculum release and operational ownership.
- **Test first / falsification:** Pending external gates cannot be silently marked complete.
- **Acceptance:** Source, native CAD, hardware and deployment evidence approved.
- **Status:** pending external team gate.

## Critical path and handover

Infrastructure → native sketch → Boolean recipes → spreadsheet dependency → capstone geometry establishes the software path. Windows connectivity → live phase evidence → measured adaptation → fabricated fit → application calibration establishes the hardware path. Public Pages depends on Build import and DevOps performance/publication gates; it does not require exposing the CAD endpoint.

Local unit tests unblock source review, not physical fabrication approval. Read QA_REPORT.md for the evidence actually obtained, and DEVOPS_HANDOFF.md for the exact outstanding procedures.
