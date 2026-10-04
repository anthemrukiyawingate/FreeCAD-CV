# Frontend TDD and simulation contracts

Task scope: **S1-DEMO, S2-DEMO, S3-DEMO, S4-DEMO**, and the integrated curriculum workbench. Implementation date: 2026-10-03. Role: Senior Graphics Programmer.

## Red → green evidence

`tests/test_demo_math.cjs` was written before any of the five HTML documents. It uses Node's built-in test runner, reads each document's single inline script, and executes that script in a `vm` context without a browser. Expected values come from independent closed-form geometry and animation identities.

Initial command, before implementation:

```text
$ node tests/test_demo_math.cjs
✖ index.html: independent geometry and animation contracts
✖ phase-1/index.html: independent geometry and animation contracts
✖ phase-2/index.html: independent geometry and animation contracts
✖ phase-3/index.html: independent geometry and animation contracts
✖ capstone/index.html: independent geometry and animation contracts
ℹ tests 5
ℹ pass 0
ℹ fail 5
Error: ENOENT: no such file or directory .../docs/index.html
[The other four cases reported their respective missing HTML paths.]
```

After implementation and additional boundary cases:

```text
$ node tests/test_demo_math.cjs
✔ index.html: independent geometry and animation contracts
✔ phase-1/index.html: independent geometry and animation contracts
✔ phase-2/index.html: independent geometry and animation contracts
✔ phase-3/index.html: independent geometry and animation contracts
✔ capstone/index.html: independent geometry and animation contracts
ℹ tests 5
ℹ pass 5
ℹ fail 0
```

The repository's `node --test tests/test_demo_math.cjs` command also exits 0. In this host's configured reporter that invocation groups the file as one passing test; the direct command above exposes all five individual document cases.

A requested p95 telemetry addition followed another red/green cycle: the new independent frame-statistics assertions first failed in all five pages with `TypeError: m.frameStatistics is not a function`; implementation then returned all five pages to green. `[10, 20, 30, 40] ms` produces a 25 ms mean, 40 FPS, and 40 ms p95; a 20-sample set with 19 intervals of 10 ms and one of 100 ms has nearest-rank p95 of 10 ms. Empty and nonfinite samples are rejected.

Browser QA found that the original 15 ms upscale threshold excluded healthy 60 Hz rendering. A regression assertion, `resolutionScale(0.5, 1000 / 60, 2) > 0.5`, failed in all five documents before the fix. The recovery threshold is now 17.5 ms; the 20 ms downscale threshold preserves hysteresis. The regression and the existing bounds/downscale tests now pass in all five documents.

## Mathematical falsification

| Contract | Independent oracle / safe failure |
| --- | --- |
| Axis-aligned rectangular sketch | All eight combinations of origin/width/height locks. Four independent parameters; origin fixes two, width and height fix one each. Locked values equal reference values, and unlocked values retain the candidate input. |
| Sketch parameter validation | Negative width throws; nonfinite coordinates and dimensions are rejected by the same finite/positive guards. |
| Circle–rectangle intersection | Half-circle, full circle, quarter-circle, disjoint shapes, tangency, rectangle wholly inside circle, and translation invariance. Absolute tolerance `1e-7 mm²`. |
| Boolean areas | Rectangle area `200 mm²` and a radius-5 half-circle give independent closed-form union, difference, and common areas. Invalid circle radius fails before drawing. |
| Plate volume | `100 × 60 × 8 − π × 5² × 8 mm³`; footprint excludes exactly one cylindrical through-hole. Hole diameter equal to or larger than the smaller plate dimension and nonfinite dimensions are rejected. |
| Hardware layout | `120 + 40 + 20 + 2 × 12 = 204 mm`; device centres are exactly `100 mm` apart. This is a labeled example fixture. |
| Time interpolation | One 1/30-second step equals two 1/60-second steps for the exponential interpolation; reduced motion returns the target immediately. |
| Dynamic resolution | Scale remains in `[0.5, min(devicePixelRatio, 2)]`, decreases when measured mean intervals exceed 20 ms, and rises when intervals are below 17.5 ms. Healthy 60 Hz / 16.67 ms rendering therefore recovers resolution after browser throttling. |
| Deployment | Every document contains one inline script and no external script or stylesheet runtime dependency. |

Tests validate the actual inline mathematics in every deployed page, avoiding a separate implementation that can drift from production. They do not substitute for browser rendering checks or native FreeCAD/OpenCascade geometry validation.

## Runtime interfaces

Every page runs one strict modular closure. `globalThis.CortexMath` is a frozen export containing the following pure, synchronous functions:

| Function | Input and return contract |
| --- | --- |
| `rectangleDOF(locks)` | `{origin, width, height}` booleans → integer 0–4. Rectangle orientation and orthogonality are already fixed by the model. |
| `constrainRectangle(candidate, locks, reference)` | Rectangle `{x, y, width, height}`, locks, and reference → validated rectangle. The UI stores the current target value when a lock is enabled. |
| `circleRectangleIntersection(rectangle, circle)` | Rectangle `{x, y, width, height}` and circle `{x, y, radius}` → exact analytic overlap area in mm², up to floating-point roundoff. Uses signed quadrant integrals of the circular segment primitive. |
| `booleanAreas(rectangle, circle)` | Same shapes → `{union, difference, intersection, rectangle, circle}` in mm². Difference means rectangle minus circle. |
| `plateProperties(parameters)` | `{width, depth, thickness, holeRadius}` → `{footprint, volume}` in mm² and mm³. |
| `layoutProperties(parameters)` | `{projectorWidth, cameraWidth, gap, margin}` → `{plateWidth, projectorCenter, cameraCenter}` in mm. |
| `lerpTime(current, target, dt, speed, reducedMotion)` | Values, elapsed seconds, inverse-second speed → exponentially interpolated value. |
| `resolutionScale(scale, frameMs, dpr)` | Current backing scale, measured mean frame interval, DPR → bounded next scale. |
| `frameStatistics(samples)` | Positive measured intervals in milliseconds → `{frameMs, fps, p95FrameMs}`, using the nearest-rank percentile. |

Browser initialization begins only after these exports, and exits immediately if `document` is unavailable. The browser renderer never sends a CAD command or makes a network request. `globalThis.CortexPerformance` is refreshed once per measured interval with `{fps, frameMs, p95FrameMs, scale, viewport, devicePixelRatio, samples, reducedMotion, phase}`; it is observable telemetry, not a performance claim. The visible FPS element's `title` also exposes sample count, mean interval, and p95 interval for read-only DOM inspection.

## Rendering, interaction, and accessibility

- Main and standalone pages expose all four phases; standalone pages open on their own phase. Local phase changes preserve focus on the initiating button and update `aria-current`.
- Sketch controls disable constrained dimensions. Unlocking the origin reveals two independent coordinate sliders; each lock fixes the current target parameter, not an arbitrary decrement of a displayed counter.
- Boolean drawing uses a dedicated offscreen canvas with `source-over`, `destination-out`, and `destination-in`. Dashed source outlines remain visible; result areas use the analytic geometry function instead of pixel counting.
- Solid dimensions ease with `1 − exp(−speed × Δt)`. Target dimensions and exact target volume update immediately, and the lesson explicitly distinguishes target geometry from the animated display.
- Phase 3 identifies the perforated plate as a browser extension of the notebook’s plain `Part::Box`. Its inspector shows the actual notebook mapping from `Dimensions.MountLength/MountWidth/MountHeight` to `Part::Box.Length/Width/Height`, alongside the corresponding plate display dimensions. The hole radius is explicitly demo-only.
- Reduced motion bypasses easing and removes the recent-edit pulse. Native range controls, labels, value descriptions, keyboard focus styles, semantic buttons, and a polite result region support keyboard and assistive-technology use.
- Responsive breakpoints move the curriculum to a top navigation strip and stack the inspector beneath the viewport. All reset buttons restore default parameters, constraints, operation, zoom, and grid visibility.
- Frame-rate output starts at `—`; it is computed from actual `requestAnimationFrame` intervals, resets after visibility changes, and never substitutes an invented 60 FPS. Scale changes are bounded and canvas backing dimensions track the viewport.
- A **60 FPS target** and scalable high-resolution drawing are implemented. Actual FPS depends on the host, refresh rate, browser, GPU, and scene; see `QA_REPORT.md` for measured browser evidence. The implementation does not lock or guarantee a refresh rate.

## Packaging and maintenance

The five documents are self-contained deployment artifacts with intentionally duplicated source. `docs/index.html` is the editing source. After changes, copy it into each phase directory, adjust `data-initial-phase` to 1/2/3/4, change the static home link to `../index.html`, and change the static standalone link to the respective `../phase-N/index.html` or `../capstone/index.html`. Re-run the five-document test suite. No build command, dependency installation, CDN, service worker, or server API is needed.

`docs/.nojekyll` supports direct GitHub Pages publication. Local preview: `python -m http.server 8000 --bind 127.0.0.1 --directory docs`. Actual publication and physical hardware fit require the separate acceptance gates documented in the root README and release QA report.
