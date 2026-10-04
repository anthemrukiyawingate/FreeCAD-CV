# CortexCAD DevOps handoff dossier

Runtime release candidate: `0.1.0rc1`; packaging correction: **intake return 2, 2026-10-04**. Current delivery checks are in [VALIDATION.md](VALIDATION.md). This is a source implementation handoff. **Build environment team owns all version control and GitHub source transition. DevOps owns all deployment environments, workstation configuration, network changes, public publication and hardware commissioning.** Development does not perform these operations. The commands below are execution instructions for the owning team, not a record that they have been run.

## 1. Ownership, inventory and go/no-go

| Area | Accountable team | Required handover evidence |
| --- | --- | --- |
| Source transfer, Git history, branches, tags, CI policy | Build environment | Archive checksum, reviewed diff, repository URL, source revision |
| FreeCAD, addon, Python runtimes and endpoint | DevOps | Version inventory, addon revision, ping and live CAD checks |
| SSH, firewall, account and secret management | DevOps | Approved source addresses, route, token storage, service owner |
| Jupyter and Claude Code workstation integration | DevOps | Kernel version, CLI version, MCP discovery and smoke results |
| GitHub Pages publishing settings and rollback | DevOps, using Build-provided branches | Pages URL, source branch, successful deployment record |
| Projector/webcam measurements and fabrication | Hardware integrator with DevOps | Device models, measured drawing, fasteners, fit results |
| Lesson acceptance and source defects | Curriculum/QA | Local checks, real-CAD results, teaching review |

Populate a deployment inventory before commissioning; placeholders are intentionally unassigned:

```text
Release/source SHA:           __________
Linux OS / hostname:          __________
Linux Python / Jupyter:       __________
Claude Code version:          __________
MCP SDK version:              __________
Windows OS / hostname:        __________
FreeCAD / native Python:      __________
FreeCADMCP addon commit:      __________
Upstream server commit:       __________ (only if using upstream server)
Linux source IPv4:            __________
Windows private IPv4:         __________
SSH account / key reference:  __________ (reference only; never a private key)
Bridge bind / forwarded port: __________
Token vault reference:        __________ (never paste token into this file)
Projector make / model:       __________
Webcam make / model:          __________
Mount substrate / fasteners:  __________
Display resolution / Hz:      __________
Camera mode / frame rate:     __________
Pages branch / URL:           __________
Responsible operator / date:  __________
```

The initial implementation cannot establish this inventory remotely. A green simulated test suite does not establish a green Windows/hardware gate. See [VALIDATION.md](VALIDATION.md) for this correction and [QA_REPORT.md](QA_REPORT.md) for historical implementation evidence.

## 2. Receive, reproduce and isolate the source

Build receives `FreeCAD-CV-intake-return-2.zip` and its sibling `.sha256` file. Verify the archive hash before extraction (`sha256sum -c …sha256` on Linux; `Get-FileHash -Algorithm SHA256` in PowerShell). The archive contains a `SHA256SUMS.json` inventory for every source file. Build compares this against extracted bytes and reviews the file changes against its existing repository for an ordinary corrective commit. The 26 tracked generated-file deletions are enumerated in `handoff/TRACKED_PATHS_TO_REMOVE.txt`; existing history and remotes are preserved. Development does not supply invented commit SHAs.

Use a dedicated checkout with no production credentials. Do not transfer `.venv`, CAD backups, Jupyter output, API keys or machine-specific settings between hosts. Linux and Windows paths are different namespaces: a Linux `/home/...` path is not a Windows FreeCAD path. CAD export and save operations run on Windows; copy resulting files through the approved file-transfer channel afterward.

Two install paths:

```bash
# Reproduce the validated dependency set if uv.lock is included.
uv sync --locked --extra dev --extra notebooks --extra mcp

# Standard Python alternative (resolves allowed ranges; capture installed versions).
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,notebooks,mcp]'
python -m pip freeze > artifacts-environment.txt
```

Run from the repository root:

```bash
python -m unittest discover -s tests -v
python scripts/validate_curriculum.py
node --test tests/test_demo_math.cjs
python scripts/execute_notebooks.py
python -m build
```

Core XML-RPC and recipe generation require only the standard library. Notebook execution, wheel building and MCP SDK checks need the respective extras. A missing optional dependency must not be reported as a passing integration test. Preserve test output with the release record.

## 3. Windows FreeCAD configuration

Install stable FreeCAD ≥1.0 with native Python ≥3.11. Record exact versions using `App.Version()` and `sys.version` from the Python console. Run the GUI under the intended non-administrator workstation account. GUI workbench execution requires that user's interactive session; a Windows service running in a different session is not a substitute.

Clone and pin the reference bridge using the Build-approved revision. Obtain the addon destination from `App.getUserAppDataDir()` and append `Mod`. Copy only `addon/FreeCADMCP` into it, restart FreeCAD, then select MCP Addon and Start RPC Server. Confirm the actual listener in Report view. [Upstream installation reference](https://github.com/neka-nat/freecad-mcp/blob/main/docs/installation.md).

Preflight checks:

- Save any existing personal work before a smoke test. Lessons create their own named documents and reject replay into an existing document.
- Close modal dialogs. Keep Report view open for exceptions.
- On Windows, `Test-NetConnection 127.0.0.1 -Port 9875` should succeed.
- In PowerShell, inspect `Get-NetTCPConnection -LocalPort 9875 -State Listen`; inspect the owning PID with `Get-Process -Id PID`. A random listener is not proof of FreeCAD.
- Run Linux `python -m cortexcad doctor` after establishing the tunnel. Capture protocol success separately from TCP reachability.
- Stop/start the addon after a setting change. Restart FreeCAD after replacing addon files.

Prefer manual startup during commissioning so readiness is visible. If DevOps elects to enable the addon's Auto-Start Server setting, verify cold boot, user login, GUI availability and tunnel reconnection. Automatic startup does not mean a recipe should run automatically.

## 4. Network configuration: recommended SSH route

```text
Jupyter / local MCP server
    → HTTP XML-RPC at Linux 127.0.0.1:9875
    → encrypted SSH forwarding on TCP 22
    → Windows 127.0.0.1:9875
    → FreeCAD GUI queue
```

Windows, elevated PowerShell (only DevOps):

```powershell
# Inspect first; installation is needed only if State is NotPresent.
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic

# Documentation-only example (TEST-NET-1); replace with the actual Linux address.
$cortexLinuxIP = '192.0.2.20'
Get-NetFirewallRule -Name OpenSSH-Server-In-TCP
Set-NetFirewallRule -Name OpenSSH-Server-In-TCP -RemoteAddress $cortexLinuxIP -Profile Private
```

If the default firewall rule is absent, create a dedicated inbound TCP 22 rule scoped to `$cortexLinuxIP` and Private profile. Review any other broad inbound SSH allow rules; a scoped rule does not negate a different broad allow rule. Do not change an existing remote access rule without retaining console access. Microsoft's [OpenSSH setup guide](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse) describes installation and service behavior.

Use key authentication under the organization's account policy. Confirm the Windows SSH host fingerprint out of band. The Windows account must be permitted to forward TCP; check `%ProgramData%\ssh\sshd_config` and the operator's effective policy if forwarding is denied. Changing this file requires service restart and DevOps change control.

Linux (documentation-only TEST-NET-1 examples; replace before use):

```bash
ip route get 192.0.2.30
ssh -N -T -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 -L 127.0.0.1:9875:127.0.0.1:9875 user@192.0.2.30
```

The addresses `192.0.2.20` and `192.0.2.30` are documentation-only TEST-NET-1 examples, not deployable endpoints. Replace both example IPs and the account with the approved environment values. No port 9875 inbound rule is needed on Windows for this route. Bind forwarding to Linux loopback explicitly. The tunnel carries a connection into the workstation; it does not copy files or launch FreeCAD. If DHCP changes the Windows address, update the inventory and tunnel target or use a reserved address. If Linux 9875 is busy, use local 19875 and set `CORTEXCAD_ENDPOINT=http://127.0.0.1:19875`.

## 5. Optional private LAN route

For a trusted private network where DevOps deliberately chooses direct TCP, use the upstream Remote Connections toggle; this binds to all interfaces (`0.0.0.0`). Set Allowed IPs to the exact Linux source address, set a long random auth token, and restart the addon. Add a source-scoped Private-profile firewall rule:

```powershell
New-NetFirewallRule -Name CortexCAD-RPC -DisplayName 'CortexCAD Linux only' `
  -Direction Inbound -Protocol TCP -LocalPort 9875 -RemoteAddress 192.0.2.20 `
  -Profile Private -Action Allow
```

Replace the documentation-only addresses in the firewall rule and endpoint before execution. Set Linux `CORTEXCAD_ENDPOINT=http://192.0.2.30:9875` and supply the same token through `CORTEXCAD_TOKEN` from the team's secret store. Upstream MCP server uses `FREECAD_MCP_TOKEN`; these are different variable names. The bridge's HTTP traffic is unencrypted, including its token. Use the SSH path across shared or untrusted networks. No public router forwarding, broad subnet default, or public Pages access to the RPC port is required. [Upstream remote settings](https://github.com/neka-nat/freecad-mcp/blob/main/docs/configuration.md).

Confirm both an allowed client and a disallowed host behave as intended. DevOps must test the actual firewall and allow-list; localhost fakes cannot validate them. Rollback: stop RPC, disable Remote Connections, restart, and disable the dedicated firewall rule.

## 6. Linux, Jupyter, Claude Code and MCP

DevOps bootstrap for an Ubuntu/Debian development host (adapt package names for the selected distribution):

```bash
sudo apt update
sudo apt install git curl openssh-client ca-certificates
# Install uv using the official installer, or use your approved package manager.
curl -LsSf https://astral.sh/uv/install.sh -o /tmp/cortexcad-install-uv.sh
less /tmp/cortexcad-install-uv.sh
sh /tmp/cortexcad-install-uv.sh
# Reopen the terminal so the installer-provided PATH is active.
uv --version
uv python install 3.12
uv sync --locked --extra dev --extra notebooks --extra mcp
source .venv/bin/activate
python --version
python -m ipykernel install --user --name cortexcad --display-name 'CortexCAD (Python 3.12+)'
```

Run `uv sync` from the extracted repository root. [Official uv installation reference](https://docs.astral.sh/uv/getting-started/installation/). The user-level kernel registration belongs to the deployment operator; CI instead uses temporary kernels.

Install Claude Code under the intended Linux user, then reopen the shell:

```bash
curl -fsSL https://claude.ai/install.sh -o /tmp/cortexcad-install-claude.sh
less /tmp/cortexcad-install-claude.sh
bash /tmp/cortexcad-install-claude.sh
claude --version
claude doctor
claude
```

Authenticate interactively with the team's authorized account. Keep credentials in the vendor or organizational secret mechanism, not a notebook. These are DevOps setup instructions; development has not installed or authenticated Claude Code on a target host.


Use Linux Python ≥3.12, not FreeCAD's embedded runtime. Install the project extras in one venv and register an ipykernel. Confirm `sys.executable` in the notebook resolves to that environment. Notebook discovery supports launching from the phase directory after installation.

```bash
source .venv/bin/activate
export CORTEXCAD_ENDPOINT=http://127.0.0.1:9875
export CORTEXCAD_TIMEOUT=5
python -m cortexcad doctor
python -m cortexcad run sketcher --dry-run
jupyter lab --ip=127.0.0.1
```

Default notebook execution is a preview. Set `CORTEXCAD_LIVE=1` deliberately for the live acceptance session. Keep Jupyter on loopback, retain its authentication, and use a separate SSH forward if another computer must access it. Do not include Jupyter tokens in Pages assets or logs.

Install Claude Code from the [vendor setup instructions](https://code.claude.com/docs/en/setup), record `claude --version`, run `claude doctor`, and authenticate with the team's authorized account. Install the `mcp` extra, then register the **absolute** executable path so changing working directories does not break it:

```bash
claude mcp add --transport stdio cortexcad -- /absolute/checkout/.venv/bin/python -m cortexcad.mcp_server
claude mcp list
```

Start Claude from an environment that has the endpoint and token. Restart its MCP connection after changing environment variables. Use `/mcp` to inspect server availability. Ask it to inspect connection readiness and preview the sketcher recipe before requesting live execution. Stdio stdout is reserved for MCP frames; diagnostics belong on stderr. [Claude Code MCP reference](https://code.claude.com/docs/en/mcp).

CortexCAD's bounded tools produce course recipes; the upstream server offers broader FreeCAD tools. When installing the upstream alternative, match the addon revision, run its external Python ≥3.12 entry point on Linux, pass its documented `--host` value, and record both revisions. Do not configure the XML-RPC port as an HTTP MCP endpoint.

## 7. Live FreeCAD acceptance session

All steps are DevOps/QA execution gates; save timestamped output and Windows screenshots.

1. Open a clean FreeCAD session. Verify GUI/native Python/addon versions, save unrelated work, and start the bridge.
2. Start the SSH tunnel. Run doctor. Stop the tunnel once to prove connection failure is bounded and visible; restore it and confirm recovery.
3. Run the Phase 1 dry-run, review script, then live run. Verify a fully constrained rectangular sketch and one valid PartDesign pad. Compare pad volume with `length × width × height` and confirm recompute assertions succeed.
4. Run Phase 2. Check union, cut and common volumes against the provided analytic identities, not just viewport appearance. Inspect each solid.
5. Run Phase 3. Verify cell aliases and the box expression links. Change the spreadsheet's width cell in FreeCAD, recompute, and check the solid updates. Restore an accepted value before export.
6. Run the capstone first with teaching fixtures only. Confirm mount/housing solids and intended voids. Repeat with measured parameters after hardware review and a clean document.
7. While a mutation is running, simulate a tunnel interruption on a disposable document. An unknown outcome must remain unknown until Windows inspection. Record whether the document exists and whether its transaction completed. Do not replay automatically.
8. Close a completed course document after saving if you intentionally want to rerun its recipe; the replay guard must reject same-name collisions. Keep original `.FCStd` evidence.
9. Record screenshots, stdout assertions, expected/actual dimensions and valid-solid checks. Approve the live gate only when these are observed on the actual Windows host.

Generated recipe code performs native checks before reporting results. Local mocked tests can verify ordering and failure handling but cannot prove the OpenCascade solver's output. Do not relabel an offline preview as a successful CAD run.

## 8. Projector and webcam integration: measurement contract

The capstone contains a parameterized mount/bracket and an open sensor housing. Exact hardware geometry cannot be inferred from a product category. Before CAD changes, collect the following with units in millimeters and retain annotated photographs/drawings:

| Item | Required measurements / constraints | How it changes the design |
| --- | --- | --- |
| Projector body | Width/depth/height, mass, center of mass, feet protrusion | Support envelope and load arm |
| Projector attachment | Hole-center coordinates, thread diameter/pitch, allowable screw engagement, manufacturer mounting orientation | Hole pattern and fastener selection |
| Projector optics | Lens center relative to body datum, throw-distance range, optical offset, focus/zoom travel | Projector location and adjustment range |
| Projector thermal paths | Inlet/exhaust faces, service/air gaps from manufacturer manual | Open faces and excluded mounting zones |
| Webcam body | Maximum envelope including clip/lens/protrusions, lens optical center | Housing cavity and optical opening |
| Webcam attachment | Tripod socket or clip geometry, thread engagement, pivot axis | Adapter or retaining method |
| Webcam view | Horizontal/vertical FOV at chosen resolution, minimum focus distance | Camera offset and working-distance range |
| Cables | Connector envelope, bend radius, USB/video/power exit direction, strain relief | Housing opening and cable keep-out |
| Structure | Material, mounting plane, edge distances, existing hole coordinates | Base thickness, bracket and hole placement |
| Fabrication | Process, material, orientation, measured dimensional error, fastener clearance | Wall thickness and tolerances |

Use a common coordinate system: base plane XY, +Z toward the devices; record the origin and axis directions on both drawings and photographs. Describe hole positions from a datum, not from arbitrary screen edges. Record measurement uncertainty and tooling (caliper, ruler, CAD vendor drawing). Check manufacturer mounting and ventilation instructions for the exact model.

The included JSON fixture demonstrates the supported family of mount and housing dimensions. It does **not** encode every device's arbitrary hole pattern, lens offset, thread, tilt adjustment, or load requirement. If the measured hardware is outside that family, file S4-ADAPT with the measured drawing, add validation/tests first, and extend the recipe; do not force a fit by falsifying dimensions. Keep the original fixture as a regression case.

## 9. Fabrication and physical fit gates

1. Select the datum and mounting orientation, make a dimensional sketch, and check available screw engagement from the equipment manual. A diameter label alone does not identify a thread.
2. Copy the example measurement JSON to a project-specific controlled record. Replace every relevant dimension with a measured value; store model identifiers and notes separately from the strict numeric recipe payload.
3. Preview and validate the JSON. Generate in FreeCAD, inspect sections around holes and cavities, and use the Measure tools to confirm pitch, clearance, wall thickness and optical opening.
4. Save `.FCStd` first. Export selected finished solids as STEP for exchange and STL only when appropriate to the fabrication workflow. Confirm millimeters at import into downstream tooling.
5. Fabricate a small hole/clearance coupon before a complete bracket. Record printer/material/orientation or machining process and adjust clearances from actual measurements.
6. Dry-fit without forcing fasteners. Confirm the housing retains the camera, cables can connect/disconnect, lens and projector paths are unobstructed, and ventilation/service access meet manufacturer requirements.
7. Verify rigidity and drift under the intended equipment load and operating temperature. The course geometry is not a structural load rating. Require the responsible hardware engineer's approval for elevated/overhead or occupied-area installations and use the organization's retention method.
8. Mark dimensions accepted only after the installed assembly remains aligned during the intended test duration. Save photographs and a fit report with pass/fail and measured deviations.

## 10. Projector display and webcam capture commissioning

The curriculum supplies hardware geometry and browser math demonstrations. A complete projection/camera computer-vision application is an integration consumer, not an implemented runtime in this release. DevOps connects it using the accepted mechanical datum and these commissioning steps:

**Projector:** connect the specified video cable to the Windows GPU, select the intended input, and use Windows Display settings to extend the desktop. Identify the projector display, select its supported native resolution and refresh rate, and record scaling. Show a full-frame grid and corner markers. Mechanically align, focus and set throw distance before recording calibration. Record any keystone or digital zoom setting; changing either invalidates projector mapping. Keep projected content clear of the lens path during setup.

**Webcam:** connect directly to an adequate USB port for first tests, confirm it in Device Manager, and enable Windows privacy access for the intended capture application. Enumerate devices by persistent identifier when supported; camera index 0 can change after reconnect. Record the chosen resolution/frame rate/pixel format. Start with the vendor camera utility or Windows Camera to confirm a stable image, then release it before the target app opens the device. Avoid simultaneous capture clients.

**Image stability:** align the camera view to include the full interaction plane and calibration markers. Fix focus, exposure and white balance when the device/SDK permits, after choosing operating illumination. If auto controls remain active, record that limitation and test lighting changes. Set projector brightness to the intended operational value before calibration. Verify neither device occludes the other and check glare/shadows at the screen edges.

**Coordinate calibration:** use a planar target with known coordinates across the interaction region. Calibrate lens distortion for the chosen camera mode, then compute camera-image-to-plane mapping from at least four non-collinear correspondences (use more to assess residuals). Map projector pixel coordinates to the same plane using a projected marker grid. A single homography is valid for a plane; depth-varying scenes need a different model. Keep camera intrinsics, image sizes, projector resolution, transforms, units, calibration date and device IDs in the consumer application's versioned calibration record.

**Acceptance:** measure held-out marker reprojection error across center and corners in both pixels and physical millimeters. Set the allowable threshold from the interaction precision requirement before the test; there is no universally correct pixel threshold. Measure end-to-end motion-to-projection latency and dropped frames over a fixed duration under load. Confirm the application handles camera disconnection and projector sleep/reconnect without moving hardware or silently using stale dimensions. Recalibrate after any mechanical movement, camera mode change, focus/zoom, keystone, display scaling or projector resolution change.

Calibration reference for an integration application: [OpenCV camera calibration](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html) and [homography concepts](https://docs.opencv.org/4.x/d9/dab/tutorial_homography.html). This delivery does not claim those application tests have been performed.

## 11. Observability, diagnosis and recovery

Keep structured client stderr logs with `operation`, `request_id`, `status`, `elapsed_ms`, `attempts` and `error_type`. The log collector should attach wall-clock timestamps; the client measures elapsed time monotonically. Store CAD payloads only in reviewed development artifacts, not routine production logs. Protect device/network inventory. Never copy tokens, private keys or full credential-bearing endpoints into issues.

| Symptom | Discriminating check | Recovery |
| --- | --- | --- |
| Immediate connection refused | Windows listener and tunnel forwarding | Start GUI/addon, correct local port, reestablish tunnel |
| SSH cannot connect | IP route, port 22 rule, host state | Fix approved route/firewall/account; retain host verification |
| TCP works, doctor fails | Owning PID, RPC response, auth header | Stop conflicting listener; correct bridge/token/protocol |
| HTTP 403 / unauthorized | Allowed IPs, token, forwarded Host | Correct allow-list/token; use loopback endpoint through SSH |
| Mutation timeout | Windows document and Report view | Inspect outcome before any rerun; restore connectivity |
| Duplicate document | Course document already exists | Save/inspect it; close intentionally before fresh run |
| Invalid dimension / JSON | Validation output and schema | Correct measured data; no network request should occur |
| Shape/solver failure | Native assertions, Report view | Preserve failing params, abort transaction, fix geometry/tests |
| MCP server exits | Venv mcp extra, absolute path, stderr | Install extra, correct interpreter/env, reconnect client |
| Jupyter wrong imports | Notebook `sys.executable` | Select CortexCAD kernel and restart it |
| Camera not available | Device Manager, privacy, capture ownership | Restore USB/permission, close competing capture app |
| Projection no longer aligned | Mechanical datum, mode/calibration record | Restore accepted settings or recalibrate |
| Pages 404 | Source branch /docs, deployment job, relative path | Build pushes branch; DevOps sets correct Pages source |
| Low demo FPS | Measured frame interval, scale, viewport/DPR | Close load, permit DRS, retest; report device limits |

Configured timeouts must be finite and greater than zero, up to 3600 seconds. They bound individual socket I/O waits, not total elapsed time under slow streaming or operating-system DNS resolution. Use numeric loopback with the SSH route for predictable addressing. Socket timeouts are not remote cancellation. The Windows queue may complete work after the client gives up. A failed network response cannot certify an untouched model. Recipes use transactions and replay guards; operators still reconcile the real document after interruption.

## 12. Pages and performance deployment gate

Build provides the accepted phase branch. DevOps selects **Settings → Pages → Deploy from a branch → that branch → /docs**, saves, and checks the generated deployment. No frontend compilation is needed. `docs/.nojekyll` is included. Check all four standalone pages and the index at the repository subpath, not only `/` on localhost. The exact selected branch must be updated manually when changing phases.

Performance test plan (DevOps/QA):

- Record OS, browser version, CPU/GPU, refresh rate, viewport in CSS pixels and device pixel ratio.
- Test 1920×1080 and 3840×2160 where hardware permits; use real fullscreen viewport dimensions for a 4K claim.
- After 5 seconds warm-up, interact continuously for 30 seconds with sliders/constraints and record frame interval p50/p95, displayed FPS, backing resolution/scale and long frames.
- Target approximately 16.7 ms/frame or faster on a 60 Hz display with DRS. Variable refresh rates and scheduling preclude an absolute locked 60+ FPS guarantee.
- Check keyboard-only controls, focus visibility, 200% zoom, mobile width and reduced-motion preference; compare displayed values with the math tests.
- Archive screenshot and metrics with device details. Do not copy a fast headless result into a hardware GPU performance claim.

Rollback Pages to the last accepted source branch and verify its deployment. Roll back a CAD integration by restoring the approved addon revision and known-good `.FCStd` backup; do not overwrite current work without preserving it. Revalidate protocol versions and repeat a small smoke test after rollback.

## 13. Release sign-off record

| Gate | Evidence | Owner / status |
| --- | --- | --- |
| Source checksum and repository import | Archive hash, revision, review | Build: pending |
| Automated source checks | QA_REPORT and CI link | Build/QA: local evidence supplied; target CI pending |
| Windows GUI and RPC | Inventory, ping, timeout/recovery | DevOps: pending |
| Four native CAD phases | Assertion output, dimensions, valid solids | DevOps/QA: pending |
| Exact hardware fit | Measured drawing, prototype report | Hardware: pending |
| Camera/projector calibration | Device IDs, modes, residuals, latency | DevOps/integrator: pending |
| Public Pages | Source branch, URL, functional checks | DevOps: pending |
| Target 4K performance | Real-device frame measurements | DevOps/QA: pending |

A release candidate can be accepted as a source handoff while deployment gates remain pending. A fully commissioned hardware curriculum release requires each applicable gate to have evidence and an accountable sign-off.
