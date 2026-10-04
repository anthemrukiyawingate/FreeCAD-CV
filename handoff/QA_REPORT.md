# CortexCAD release-candidate QA report — historical 2026-10-03 evidence

For the corrected repository layout and current intake results, see [VALIDATION.md](VALIDATION.md). The results below refer to the original implementation run and are not reruns of the intake correction.

Date: **2026-10-03**. Candidate: **0.1.0rc1**. Status: **source implementation validated for Build/DevOps handoff; commissioning gates remain open**.

Build exclusively owns Git/version-control operations and GitHub source transition. DevOps exclusively owns deployment and workstation/hardware integration. No Git repository was initialized, no commit or push was made, and no public site or Windows environment was deployed by this implementation task. The local loopback browser preview is development validation only.

## Executed validation

Host: Linux x86_64. Main validation Python **3.12.3**; Node **24.13.1**; MCP SDK **1.30.0**; JupyterLab **4.6.4**; nbclient **0.11.0**. Exact installed versions are recorded in [VALIDATED_ENVIRONMENT.txt](VALIDATED_ENVIRONMENT.txt); the source includes `uv.lock`.

| Check | Actual command / method | Observed result |
| --- | --- | --- |
| Combined Python contracts | `.venv/bin/python -m unittest discover -s tests -v` | **55 passed**, no skips, 3.439 s in final run |
| Python source lint | `.venv/bin/ruff check cortexcad scripts tests` | All checks passed |
| Lesson/static contracts | `.venv/bin/python scripts/validate_curriculum.py` | **4 notebooks, 5 pages, 0 errors** |
| Deployed JavaScript math | `node tests/test_demo_math.cjs` | **5 page cases passed**, no failures/skips; dozens of independent assertions per page |
| Real Jupyter execution | `.venv/bin/python scripts/execute_notebooks.py` | All four notebooks executed in separate temporary offline kernels from their lesson directories |
| Native syntax compatibility | Recipe tests using Python 3.11 AST grammar | All four generated scripts parse; this is not FreeCAD execution |
| Python distribution build | `.venv/bin/python -m build --no-isolation` | Wheel and sdist built successfully using setuptools 84.0.0/wheel 0.48.0 |
| Installed artifact smoke | Clean Python 3.12 venv, wheel-only install with no dependencies; CLI run from `/tmp` | All four dry-run recipes return `status=offline`, `success=false`, and a compiled source preview |
| Browser interaction | Codex in-app browser, real controls and DOM inspection | Locks, keyboard ranges, phase changes, all four standalone routes and model readouts checked |
| Responsive layout | 390×844 and 3840×2160 viewport overrides | No horizontal document overflow in the inspected capstone view; overrides reset afterward |
| Browser diagnostics | Captured warning/error log query after interaction | Empty warning/error list at inspection |

The 55 Python tests comprise **22 client/CLI**, **10 MCP**, **16 recipe/notebook**, **4 delivery** and **3 task-harness** cases. IPC tests use actual local XML-RPC sockets, faulting fake servers and an actual MCP stdio SDK client session. They do not contact a Windows workstation. Source notebook outputs remain empty after execution because the validation runner executes copies in memory.

Dependency installation initially encountered the sandbox's network restriction, then completed with approved package-registry access. Loopback tests and Jupyter kernels ran with approved local socket access. The first nonisolated package build lacked its backend; installing setuptools/wheel from the existing local cache resolved that setup issue. The final package build and clean-wheel smoke both passed.

## Test-first evidence and defects found

- [IPC_TDD.md](IPC_TDD.md): initial missing-implementation failures; actual refused connections, timeout, lost responses, malformed XML/result schema and RPC faults. Python XML-RPC's implicit retry was disabled to prevent replay after a dropped connection.
- SDK parameter coercion initially accepted boolean dimensions; preserving raw JSON types before validation fixed the recorded failing regression.
- Final boundary review added three tests: duplicate JSON keys now fail in the CLI, and MCP live execution requires an exact boolean. Strings, numbers and null fail before constructing a live client.
- [CURRICULUM_TDD.md](CURRICULUM_TDD.md): parameter contracts, overlapping-hole regression, replay protection, abort/recompute control flow and unrelated-directory notebook execution.
- [FRONTEND_TDD.md](FRONTEND_TDD.md): all five documents initially absent; analytic intersection/volume/DOF identities subsequently pass. Added independently tested p95 statistics.
- Browser review found DRS could decrease during a slow interval but could not recover on a 60 Hz display with a `<15 ms` recovery threshold. A regression failed first; recovery now uses `<17.5 ms`, with downscaling above 20 ms and bounded scale.
- Browser/static review corrected standalone relative links and the Phase 3 explanatory mapping. The notebook's plain expression-driven box and the browser's perforated-plate extension are now distinguished explicitly.
- [DELIVERY_TDD.md](DELIVERY_TDD.md): missing modules initially failed; notebook outputs, syntax, external assets, broken links, symlinks/private env files and unknown task IDs are checked.

## Browser observations

1. Phase 1 starts with the origin fixed and **2 DOF**. Enabling width and height locks shows **0 DOF / fully constrained** and disables both range inputs. Reset restores default state.
2. Phase 2 intersection with circle offset moved to 100 mm reports **0 mm²**. The independent analytic tests also cover containment, tangency, disjoint regions and translation.
3. Phase 3 plate width moved from 80 to 160 mm, with depth 65 mm, thickness 9 mm and radius 9 mm, updates exact target volume to **91,309.8 mm³**, consistent with `(160 × 65 − π × 9²) × 9`.
4. Capstone projector width changed from 120 to 121 mm through a keyboard arrow; required plate width changed from **209 to 210 mm**. The page visibly labels these as example, unmeasured dimensions.
5. All standalone links were opened: `/phase-1/index.html`, `/phase-2/index.html`, `/phase-3/index.html`, `/capstone/index.html`; each initializes its own lesson and maintains working relative navigation.
6. At 390 px width, the inspected document width was 375 px (scrollbar accounted for), with a 347 px canvas CSS width; controls stacked below the view. At 3840×2160, document width was 3840 px and the rendered view used a 1726×720 CSS-pixel scene. The design deliberately limits workbench width; a 4K viewport does not imply every canvas fills the screen.

### Performance result: target not certified

The UI reports actual requestAnimationFrame intervals, including mean and p95, and DRS responds to those measurements. The automated in-app browser showed variable scheduling: one ordinary-viewport sample displayed 56 FPS; a later **3840×2160 sample measured 2 intervals with mean 590.75 ms, p95 991.80 ms, displayed 2 FPS and DRS 0.50×**. That sample **does not pass a 60 FPS gate**. Browser/automation throttling may contribute, but the cause was not established and these numbers are not promoted as a target-device benchmark.

The source implements time-based easing, reduced-motion bypass and tested DRS recovery. A sustained 30-second target-device interaction benchmark, actual GPU/refresh inventory, and a reduced-motion UI preference check remain for DevOps/QA. Reduced-motion math is tested locally; no operating-system preference was changed during browser QA. The release does not claim a locked or universal 60+ FPS rate.

## Falsification and limits at the IPC boundary

| Scenario | Local outcome established | What it does not prove |
| --- | --- | --- |
| Invalid dimensions, unexpected keys, duplicate JSON keys | Rejected before IPC | Suitability of an accepted dimension for a real device |
| Missing listener | Offline result and non-success exit | Actual Windows firewall or route policy |
| Timeout or response lost after mutation request | Unknown outcome, one request only, no retry | Remote cancellation or rollback |
| RPC fault / malformed response | Non-success outcome with redacted diagnostics | That the Windows document is untouched |
| Explicit upstream script failure | Error, or unknown for GUI timeout | Whether partial native changes persist |
| Existing course document | Generated script refuses replacement using an API double | Real native solver behavior |
| Exception during object creation | Abort transaction then recompute observed in a double | A disconnect reaching the remote exception handler |
| MCP discovery and invocation | Real stdio handshake and bounded tools | Actual model provider/Claude account setup |

Configured network timeouts are finite per-I/O bounds, not total wall-clock deadlines for DNS or slow-stream responses. Workstation inspection is required after uncertain mutations. FreeCAD API doubles deliberately do not fabricate successful solids or constraint-solver results.

## Outstanding team-owned acceptance gates

| Gate | Owner | Status / required evidence |
| --- | --- | --- |
| Source import, branches, CI execution in managed repository | Build | Pending; checksum, reviewed revision, target CI record |
| Windows FreeCAD/native Python/addon compatibility | DevOps | Pending; versions, live ping, GUI-dispatch and recovery evidence |
| All four real native CAD recipes | DevOps + QA | Pending; native assertions, solver result, solid validity and analytic volumes |
| Actual projector/webcam geometry | Hardware integrator + DevOps | Pending; complete measurements, supported-family review/adaptation |
| Fabricated fit, retention, load and thermal/optical clearances | Hardware engineer | Pending; prototype and installation acceptance |
| Projector/camera application and calibration | DevOps + application integrator | Pending; consumer application, device modes, residuals, latency and disconnect handling |
| Target-device performance and full accessibility sign-off | DevOps + QA | Pending; sustained performance and assistive-technology/preference tests |
| Public Pages release | DevOps | Pending; Build-provided branch, Pages URL and deployment/rollback verification |

The [DevOps dossier](DEVOPS_HANDOFF.md) supplies the detailed integration/configuration procedures, and the [Build handoff](BUILD_HANDOFF.md) specifies source transfer and repository ownership. Exact hardware fit and a commissioned public release are intentionally not represented as completed work.
