# FreeCAD-CV intake return 2 validation

Date: 2026-10-04. Scope: CV-1, CV-3, CV-4, CV-8 only. This document records validation of the corrected, extracted delivery tree. The results below were obtained from a source archive extracted into a new scratch directory, without access through a parent repository layout.

The original 2026-10-03 results are retained in [QA_REPORT.md](QA_REPORT.md) as historical evidence. L.A. independently reproduced 51 passed and four optional MCP-SDK skips in Python 3.12. Neither run establishes live FreeCAD, hardware, browser performance, or deployment acceptance.

## Test-first evidence

The new release tests first failed importing the absent release guard. After implementing the guard and archive API, the eleven release tests reported 10 failures and two errors against the uncorrected layout. They exposed tracked bytecode, missing repository-root files and missing handoff documents. Tests include rejection of deleted-but-still-tracked generated paths and links that escape the repository even when their target exists.

## Validation mode

In a Git checkout, the hygiene test reads that root's `git ls-files -z` inventory, including files deleted from the working tree but still in the index. It does not change the index or walk up to a parent repository. In a source archive, it checks `SHA256SUMS.json`, the inventory embedded in that delivered root. Missing inventories fail. These modes are reported separately.

Build's existing index retains the 26 paths in [TRACKED_PATHS_TO_REMOVE.txt](TRACKED_PATHS_TO_REMOVE.txt) until Build records their deletions. The current checkout's tracked-file test must remain red until then; the cleaned archive can pass its own inventory checks. This distinction is deliberate and must not be reported as a clean committed-tree result.

## Current execution results

| Check | Executed result |
| --- | --- |
| Fresh Python 3.12.3 environment, no optional SDK; full suite from extracted root | **66 discovered: 62 passed, 4 skipped, 0 failures** (0.460 s). The four skips are the optional real-MCP SDK tests. |
| Separate fresh Python 3.12.3 environment, installed from extracted root with the delivered MCP pin | **66 passed, 0 skipped, 0 failures** (2.128 s), using MCP SDK **1.30.0**. |
| New release tests within both extracted-tree suites | **11 passed**: inventory hygiene, root files, ignore categories, link containment, example addresses, deleted tracked entries, manifest containment, missing-inventory rejection and archive layout/checksums. |
| Static curriculum validator from extracted root | **4 notebooks, 5 pages, 0 errors**. This is a structure/syntax check, not notebook or browser execution. |
| Ruff on extracted `cortexcad`, `scripts`, `tests` | All checks passed. |
| Delivered dependency lock | `uv lock --check --offline` passed. |
| Existing working-tree release suite | **10 passed, 1 expected failure** because Build's unchanged index still tracks the 26 removed bytecode files. |
| Version-control preservation | The index file's bytes match the pre-correction checksum; no staged change, commit or history operation was made. |

The original 55 tests are preserved; the correction adds 11 release tests. The fresh baseline count therefore advances from L.A.'s 51 passes plus four skips to 62 passes plus four skips. SDK installation used only the delivered repository root and the `mcp` extra; no manual package path was needed.

Commands executed with the chosen fresh environment's `python`, from the extracted `FreeCAD-CV/` root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python scripts/validate_curriculum.py
ruff check --no-cache cortexcad scripts tests
uv lock --check --offline
```

For the SDK environment, the source was first installed with `uv pip install --offline --python CLEAN_ENV_PYTHON -e '.[mcp]'`. It resolved MCP 1.30.0 within the delivered `<2` constraint. Both environments were newly created with Python 3.12.3. `PYTHONPATH` was unset, and the SDK suite exercised actual loopback XML-RPC and stdio.

Capture logs have workspace/extraction/environment paths scrubbed before being saved: [baseline suite](validation/python-core.txt), [SDK suite](validation/python-mcp.txt). The final source archive contains only repository-local documents and an embedded file-checksum inventory. Archive integrity is verified again after the final evidence files are included.

## External gates

Windows-native CAD, projector/webcam physical fit, calibrated application behavior and public deployment remain pending with their existing owners. Node/browser/Jupyter/native suites are not repeated for these packaging and documentation corrections unless explicitly recorded below.
