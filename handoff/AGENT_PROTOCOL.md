# Agent deployment and TDD protocol

The project brief explicitly authorized independent AI Developer agents. Three source agents were dispatched alongside architecture/integration work; no user-owned task, external message, Git branch or deployment was created by that dispatch.

| Workstream | Owned outputs | Bounded scope |
| --- | --- | --- |
| IPC / QA | client, CLI, MCP wrapper, IPC tests and interface docs | Linux protocol boundary and falsification |
| Curriculum / CAD | native recipe generator, four notebooks, lessons and hardware contracts | Parameterized geometry and teaching material |
| Graphics | five standalone HTML pages, math tests and frontend evidence | Local engine mocks and rendering |
| Lead architecture / QA | README, packaging, backlog, handovers, CI and integration evidence | Source integration and release handoff |

## Zero-assumption task packet

Every packet states owner, prerequisite artifacts, dependency IDs, output paths, validation cases and acceptance. `handoff/tasks.json` is the machine-readable registry; `BACKLOG.md` presents the same task definitions for planning. Emit a packet with:

```bash
python scripts/task_harness.py S0-IPC
python scripts/task_harness.py S1-DEMO
python scripts/task_harness.py S4-FIT
```

The packet begins with the requested exact engineering template:

> As a Senior AI Developer and QA Auditor, execute [TASK ID]. 1) Define tests. 2) Implement logic adhering to the EajR Signature. 3) Document interfaces. 4) Package for dynamic deployment. 5) Provide a QA Falsification audit proving safe failure modes across the Linux/Windows IPC boundary.

Graphics packets add the Senior Graphics Programmer role and require single-file HTML, requestAnimationFrame, dynamic resolution scaling and lerped controls. The harness **prints instructions**. It does not silently invoke an AI CLI, spend API usage, execute arbitrary task text or deploy code.

## Execution order

1. Read the task, README and relevant interface. Confirm inputs exist; explicitly record missing measured data or hardware access.
2. Write a falsifying contract test, run it, and capture the actual failure. Import failures establish missing implementation; behavioral regressions must establish the actual wrong behavior.
3. Implement the smallest complete behavior and pass the test. For FreeCAD, separately distinguish local script-contract tests from native solver checks.
4. Test failure modes at the boundary: invalid data, connection refusal, interrupted mutation, server fault, malformed reply and replay. Do not auto-retry a mutation after uncertainty.
5. Document interface and package the code. Review shared files only after the owning agent completes; coordinate changes rather than overwriting ongoing work.
6. Run integration checks once against the combined source. Fix failures and rerun affected checks. Preserve actual results and limitations in QA_REPORT.md.
7. Hand source to Build. DevOps performs workstation/network/hardware/Pages work and supplies the corresponding gate evidence.

## EajR Signature review contract

Python automation targets 3.12+; generated native scripts parse under 3.11. Public interfaces and helper functions have explicit types. Numeric parameters reject strings, booleans, unknown keys, NaN, infinity and impossible relationships. Scripts create controlled documents, use transactions, explicitly recompute before reads, validate shapes and refuse unintended replay. Every notebook starts with `[CAPSTONE INTEGRATION TARGET]` and defaults to a clearly labeled offline preview. Network operations have finite configured timeouts and structured redacted diagnostics. Unknown outcomes stay unknown until reconciliation on Windows.

## Evidence index

- `IPC_TDD.md`: failed import, transport behavior, malformed replies, SDK and retry regressions.
- `CURRICULUM_TDD.md`: parameter and generated-script contracts, native checks awaiting execution.
- `FRONTEND_TDD.md`: math red/green records and rendering limitations.
- `DELIVERY_TDD.md`: source-package, notebook/static and task-packet tests.
- `QA_REPORT.md`: integrated results, browser checks, package inventory and external gates.

A task's existence in the backlog is not proof that a deployment ran. The registry explicitly labels external-team gates pending. Only the responsible team may close them with real environment evidence.
