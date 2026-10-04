# CortexCAD: A Parametric FreeCAD Curriculum

Build a constrained sketch, turn it into a solid, drive it with data, and integrate the result into a projector and webcam installation. CortexCAD joins Linux-hosted Jupyter and AI tools to a Windows FreeCAD execution engine, with independent browser simulations for every phase.

**Release status:** source release candidate for Build and DevOps handoff. The Build environment team exclusively owns version control and the GitHub transition; DevOps exclusively owns the deployment environment. Live Windows integration, measured hardware fit, and public GitHub Pages publication are separate acceptance gates. Example dimensions are teaching fixtures, never claims of compatibility with a particular device. See [intake return 2 validation](handoff/VALIDATION.md) for checks of the corrected delivery and [original QA evidence](handoff/QA_REPORT.md) for the earlier implementation results.

## Acknowledgements and licensing

Curriculum design acknowledgement: **etherwAre**. Original CortexCAD curriculum, code, and demos are released under the [MIT License](LICENSE). The **Plato Shadows capstone project concept is an original idea by Tee Ken Ng, [@TeeKenNG on TikTok](https://www.tiktok.com/@teekenng)**, credited as requested by the project brief. This curriculum is an independent educational implementation; attribution does not imply endorsement or license any third-party artwork. FreeCAD and the selected MCP bridge retain their own upstream licenses.

## Repository map

```text
FreeCAD-CV/
├── README.md
├── LICENSE
├── .gitignore
├── uv.lock
├── pyproject.toml
├── docs/                                      # GitHub Pages source; zero build
│   ├── index.html                             # Interactive curriculum workbench
│   ├── phase-1/index.html                     # Sketch constraints and degrees of freedom
│   ├── phase-2/index.html                     # Boolean set operations
│   ├── phase-3/index.html                     # Parameter changes and recompute
│   ├── capstone/index.html                    # Hardware layout engine mock
│   └── .nojekyll
├── 01_Phase1_Sketcher_and_PartDesign/           # Lesson, notebook, acceptance criteria
├── 02_Phase2_Constructive_Solid_Geometry/      # Cuts, unions, intersections
├── 03_Phase3_Python_API_and_Spreadsheets/      # JSON → aliases → expressions → recompute
├── Projects/
│   ├── mini_projects/
│   └── CAPSTONE_Plato_Shadows_Hardware_Mounts/ # Parametric fixtures and measurement contract
├── cortexcad/                                 # Typed Linux client and FreeCAD-native recipes
├── scripts/                                   # Validation, preview, release and task harness
├── tests/                                     # Failure-first IPC and geometry-contract tests
├── handoff/
│   ├── BUILD_HANDOFF.md                       # Source transfer and version-control ownership
│   ├── BACKLOG.md                             # Sprint 0–4, dependencies and exit gates
│   ├── DEVOPS_HANDOFF.md                      # Operations, recovery and release runbook
│   ├── AGENT_PROTOCOL.md                      # TDD task packets and deployment contracts
│   ├── QA_REPORT.md                           # Historical implementation evidence
│   ├── VALIDATION.md                          # Corrected delivery validation
│   └── TRACKED_PATHS_TO_REMOVE.txt            # Generated files for Build to remove
└── .github/workflows/ci.yml                    # Python, notebook and demo checks
```

## Architecture and runtime boundary

```text
Linux development host                       Windows execution workstation
┌──────────────────────────┐                 ┌────────────────────────────┐
│ Jupyter · Python ≥3.12    │  SSH tunnel     │ FreeCAD ≥1.0 GUI          │
│ CortexCAD XML-RPC client ├────────────────►│ FreeCADMCP addon          │
│                          │ localhost:9875  │ Python ≥3.11 native API   │
│ Claude Code / MCP SDK    │                 │ GUI-thread CAD execution │
│   └─ local MCP stdio     │                 └────────────────────────────┘
└──────────────────────────┘
Browser → docs/index.html → local math simulations (no workstation connection)
```

The reference bridge is [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp). Its Windows addon offers **XML-RPC on TCP 9875**. MCP is a separate protocol, normally spoken over stdio between an AI client and its local server. Port 9875 is not an MCP HTTP/SSE endpoint. CortexCAD provides a typed direct XML-RPC path for notebooks and an optional local MCP wrapper. Raw socket bridges need a separate adapter; sending XML-RPC to an unrelated socket protocol is unsupported.

Keep two Python environments: Linux Python **3.12+** for automation, Jupyter and MCP; FreeCAD's bundled Python **3.11+** for geometry. Never pip-install a system FreeCAD substitute into the notebook environment. Check the embedded version in FreeCAD's Python console:

```python
import sys
import FreeCAD as App
print(sys.version)
print(App.Version())
```

## Start here: local curriculum and demos

From a clone or extracted repository root, with Python 3.12+ and Git installed:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,notebooks,mcp]'
python -m unittest discover -s tests -v
python scripts/validate_curriculum.py
node --test tests/test_demo_math.cjs
python -m http.server 8000 --bind 127.0.0.1 --directory docs
```

Open [the local playground](http://127.0.0.1:8000). If port 8000 is occupied, `python scripts/preview.py` selects a free loopback port and prints its URL. The browser demos require no npm install, bundler, cloud service, account, or CAD connection. Node is only needed for their automated math tests. If `python3` is older than 3.12, install a supported Python through your distribution or `uv python install 3.12`, then use `uv venv --python 3.12`.

Start notebooks from the repository root in another terminal:

```bash
source .venv/bin/activate
python -m ipykernel install --user --name cortexcad --display-name 'CortexCAD (Python 3.12+)'
jupyter lab
```

Choose that kernel and open the phase notebook. Default execution is an offline preview: it validates parameters and shows the FreeCAD script without claiming to create geometry. Enable live execution only after the connection checks below.

## Windows: install and start the CAD engine

1. Download a stable Windows build from [FreeCAD's official downloads](https://www.freecad.org/downloads.php). Install FreeCAD 1.0 or newer, launch it once, and record the exact FreeCAD and embedded Python versions. Prefer a stable build over a weekly build.
2. Install Git for Windows. Clone the bridge with `git clone https://github.com/neka-nat/freecad-mcp.git`. Record `git -C freecad-mcp rev-parse HEAD` in the release evidence. Pin the same reviewed revision on both machines if you use the upstream MCP server.
3. Open **View → Panels → Python console** in FreeCAD. Run the following to discover the actual addon directory rather than assuming a version-specific path:

   ```python
   import os
   print(os.path.join(App.getUserAppDataDir(), 'Mod'))
   ```

4. Copy the cloned `addon/FreeCADMCP` directory into that `Mod` directory. Verify that `Mod/FreeCADMCP/InitGui.py` exists directly; avoid a nested copy of the repository. Common paths include `%APPDATA%\FreeCAD\v1-1\Mod` and older `%APPDATA%\FreeCAD\Mod` installations.
5. Restart FreeCAD, select **MCP Addon**, and click **Start RPC Server**. Keep FreeCAD open. In **Report view**, confirm the listener address, port, and successful startup. The upstream default is loopback `127.0.0.1:9875`.
6. In PowerShell, run `Test-NetConnection -ComputerName 127.0.0.1 -Port 9875`. A TCP success only proves a listener exists; the Linux `doctor` command below checks the protocol. Modal dialogs or a blocked GUI can prevent geometry commands from completing.

This course uses the upstream workbench; no custom background-thread macro is required. If using another macro, verify its transport and methods before connecting. See the upstream [installation guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/installation.md) for packaging differences.

## Linux → Windows: secure routing and connection

The recommended route keeps the executable-code bridge on Windows loopback and forwards it over SSH. Install and enable Windows OpenSSH Server using [Microsoft's setup instructions](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse). Use a dedicated workstation account and SSH keys. Limit the Windows SSH inbound firewall rule to the Linux host or trusted private subnet; do not open 9875 to the public internet.

Determine the Windows private IPv4 address with `ipconfig`, and Linux routing with `ip route get WINDOWS_IP`. Replace `WINDOWS_USER` and `WINDOWS_IP` with your own values. In a persistent Linux terminal:

```bash
ssh -N -T -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 -L 127.0.0.1:9875:127.0.0.1:9875 WINDOWS_USER@WINDOWS_IP
```

If Linux port 9875 is occupied, change only the first port to 19875 and update the endpoint below. Verify the SSH host fingerprint through a trusted channel on the first connection. Keep this terminal open while running lessons.

```bash
source .venv/bin/activate
export CORTEXCAD_ENDPOINT=http://127.0.0.1:9875
export CORTEXCAD_TIMEOUT=5
python -m cortexcad doctor
python -m cortexcad run sketcher --dry-run
python -m cortexcad run sketcher --live
```

Notebook live execution uses `CORTEXCAD_LIVE=1`; set it before starting Jupyter or explicitly in the notebook setup cell after reviewing the generated script. A timed-out mutation has an **unknown outcome**: inspect the Windows document before attempting another run. Never blindly retry a geometry mutation.

For a direct private-LAN connection, follow the bridge's current [remote configuration](https://github.com/neka-nat/freecad-mcp/blob/main/docs/configuration.md): Remote Connections binds to all interfaces (`0.0.0.0`); restrict Allowed IPs to the Linux source, configure an auth token, and scope the inbound Windows firewall rule to that IP, port, and Private profile. Supply the token using `CORTEXCAD_TOKEN` in the Linux environment. Stop the RPC server before changing its bind configuration, restart, and verify the listener. A firewall allow-list does not encrypt traffic; use the SSH route for shared networks. No router port forwarding is required. Full commands and fault diagnosis are in the [DevOps dossier](handoff/DEVOPS_HANDOFF.md).

## Linux AI tools and MCP

Install Claude Code using the vendor's [Linux setup instructions](https://code.claude.com/docs/en/setup), then run `claude --version`, `claude doctor`, and `claude` to authenticate with your own account. The curriculum and browser demos also work without an AI subscription.

CortexCAD's optional MCP SDK dependency is installed by the `mcp` extra above. Its local stdio server uses the same timeout and validation policy as the notebook client. With the tunnel running, register it using the actual absolute path to the checkout:

```bash
claude mcp add --transport stdio cortexcad -- /absolute/checkout/.venv/bin/python -m cortexcad.mcp_server
claude mcp list
```

This wrapper exposes bounded curriculum operations. To use the broader upstream tool surface instead, install the upstream server in a separate Python 3.12+ environment and follow its documented endpoint configuration; record its exact revision alongside the addon. Do not run the upstream MCP package inside FreeCAD's bundled interpreter.

## Phases and learner branch workflow

The commands in this section are instructions for the Build environment team and learners operating under its policy. Development supplies the source; it does not initialize, commit, push or manage the repository. See the [Build handoff](handoff/BUILD_HANDOFF.md).

| Sprint | Phase | Deliverable | Browser engine mock | Exit evidence |
| --- | --- | --- | --- | --- |
| 0 | Infrastructure | Environment, bridge, CI, handoff | Curriculum workbench | Offline tests and connection checklist |
| 1 | Sketcher & PartDesign | Constrained rectangular profile and pad | Degrees of freedom and locks | Solver and pad volume checks |
| 2 | Constructive Solid Geometry | Union, cut and common | Overlapping-shape set operations | Boolean volume identities |
| 3 | Python API & Spreadsheets | Validated JSON, cell aliases, expressions | Sliders and interpolated recompute | Dimensions and volume track input |
| 4 | Plato Shadows Hardware | Mount and sensor housing parametrization | Hardware layout and clearance | Measured fit, valid solids, integration record |

This repository already belongs to Build's version control. Return additions, document moves and the listed generated-file deletions for an ordinary corrective commit. Preserve existing history and remotes. The phase workflow below remains a learner procedure managed by Build.

For each phase, create its branch from the last accepted phase, run its notebook, collect evidence, then publish that branch:

```bash
git switch -c phase-1-sketcher
# Complete Phase 1; run the validation commands above.
git add .
git commit -m 'Complete Phase 1 sketch and pad'
git push -u origin phase-1-sketcher
```

Use `phase-2-csg`, `phase-3-python-spreadsheets`, and `phase-4-capstone` for subsequent phases. Keep `docs/` in every branch. Review differences before merging an accepted phase back to `main`; never overwrite another learner's branch.

## Publish GitHub Pages from the active phase

DevOps performs these deployment steps using the branch supplied by Build. This source handoff does not publish a site or change the deployment environment.

1. Push the desired phase branch to GitHub; local checkout alone is insufficient.
2. Open the repository's **Settings → Pages**.
3. Under **Build and deployment**, select **Deploy from a branch**.
4. Choose your current phase branch and the **/docs** folder, then **Save**.
5. Wait for the Pages deployment in **Actions** to succeed. Open the URL reported by Pages and verify all four phase links, controls, and a mobile layout.
6. On a phase change, manually select the new branch in Pages settings. GitHub does **not** track your local active branch automatically.

The same `/docs` site includes every phase as a standalone HTML document and an integrated landing workbench. Relative links support project URLs such as `https://OWNER.github.io/REPOSITORY/`. Reverting the Pages source to the last accepted branch is the rollback procedure. See [GitHub's publishing-source guide](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## EajR Signature and agent execution

- Type Python interfaces explicitly. Keep generated native scripts compatible with Python 3.11.
- Recompute the active FreeCAD document after geometry changes and before reading results or exporting. Use document transactions and validate final shapes.
- Start **every notebook** with `[CAPSTONE INTEGRATION TARGET]`, explaining that lesson's contribution to the final installation.
- Validate finite positive dimensions and geometric relationships before IPC. Never interpolate unvalidated user text as executable Python.
- Use explicit network timeouts, structured diagnostic logs, and separate offline previews from live success. Do not log credentials or entire executable payloads.
- Define falsifying tests before implementation. Retain red/green evidence, document interfaces, and label simulated versus real-CAD coverage.

Agent task packet:

> As a Senior AI Developer and QA Auditor, execute [TASK ID]. 1) Define tests. 2) Implement logic adhering to the EajR Signature. 3) Document interfaces. 4) Package for dynamic deployment. 5) Provide a QA Falsification audit proving safe failure modes across the Linux/Windows IPC boundary.

Graphics task packet:

> Role: Senior Graphics Programmer. Task Target: Implement the standalone HTML for Phase [X]. Use a requestAnimationFrame loop, Dynamic Resolution Scaling, and time-based interpolation in a modular JavaScript closure. Accurately simulate the concept taught in the corresponding notebook, with a 60 FPS target and measured performance evidence.

The [complete backlog](handoff/BACKLOG.md) defines test-first task packets, dependencies and acceptance gates. The [agent protocol](handoff/AGENT_PROTOCOL.md) describes dispatch and the [DevOps dossier](handoff/DEVOPS_HANDOFF.md) covers installation, observability, incident handling, rollback and release sign-off.

## Performance and physical validation

The demos use a dark `#21252B` foundation, scalable canvas graphics, frame-budget feedback, dynamic backing resolution, and interpolated controls. “4K video game fidelity” is the visual target. Refresh rate, GPU and browser scheduling set the achievable FPS; 60 FPS cannot be guaranteed on every device. Record viewport, device pixel ratio, interaction, frame timing and scale before claiming a performance pass. These browser engine mocks do not run OpenCascade or prove a real CAD solid is manufacturable.

Exact capstone mounts require measured device dimensions, mounting patterns, cable and optical clearances, manufacturing tolerances, fasteners, and mounting-load assumptions. Replace the labeled example measurement fixture, regenerate, inspect in FreeCAD, and test a physical prototype before marking the capstone accepted. No hardware measurements or workstation access were included in the initial request.
