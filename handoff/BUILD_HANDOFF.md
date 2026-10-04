# FreeCAD-CV Build handoff — intake return 2

Date: 2026-10-04. Applicable returns: CV-1, CV-3, CV-4 and CV-8. The runtime remains `0.1.0rc1`; this is a source/layout correction to the existing repository. Build exclusively owns version control and commits. DevOps owns deployment. No index, branch, commit, remote or history was changed by the correction task.

## Files returned for Build to commit

- Repository-root `.gitignore` covers bytecode, caches, virtual environments, `*.egg-info`, dependencies and build outputs.
- [TRACKED_PATHS_TO_REMOVE.txt](TRACKED_PATHS_TO_REMOVE.txt) contains the exact 26 tracked generated paths to remove. Their files are deleted from the working tree; their index entries remain for Build to record in an ordinary commit. No tracked `*.egg-info` was found in FreeCAD-CV.
- Root `LICENSE`, `uv.lock` and `.env.example` are copied into this repository from their former outer location. No file in the handoff depends on the outer copies.
- All former `engineering/` documents and the task registry move to `handoff/`. README links and the task harness use that location. [VALIDATION.md](VALIDATION.md) is the current delivery validation record; [QA_REPORT.md](QA_REPORT.md) retains the dated original evidence.
- Dossier examples use documentation-only TEST-NET-1 addresses. Operators must replace these before use.
- `scripts/release_guard.py`, `tests/test_release.py` and the updated packager reject generated inventory entries, require root files, check local links and validate the archive layout.

Review the tracked document deletions together with the new `handoff/` files as moves. The [correction receipt](INTAKE_RETURN_2.md) records the baseline and scope. Return any questions through Build. Existing history is preserved; these corrections require no rewrite.

## Delivered tree and checksum

The corrected archive is `FreeCAD-CV-intake-return-2.zip`, with a sibling `.sha256`. The archive has exactly one root, `FreeCAD-CV/`, containing source, `LICENSE`, `.gitignore`, `uv.lock`, `handoff/`, and the embedded `SHA256SUMS.json` file inventory. Git metadata, bytecode, caches, virtual environments, generated package metadata and build output are excluded.

Verify the sibling hash, extract into a fresh directory, and verify each inventory entry from the extracted root:

```python
import hashlib
import json
from pathlib import Path
root = Path.cwd()
inventory = json.loads((root / 'SHA256SUMS.json').read_text())
for relative, expected in inventory.items():
    path = (root / relative).resolve()
    assert path.is_relative_to(root.resolve()), relative
    assert path.is_file(), relative
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, relative
print(f'Verified {len(inventory)} files')
```

Apply the source additions, modifications, moves and listed deletions to the existing managed checkout. Do not treat the extracted archive as a replacement Git history. Its checksum inventory is transport evidence; subsequent edited sources require newly generated checksums.

## Reproduce the correction checks from the delivered tree

Run from the extracted `FreeCAD-CV/` root, not its parent. Python 3.12+ is required. A clean standard-library environment supports the baseline suite; four real MCP SDK tests are intentionally skipped when the optional SDK is absent.

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python scripts/validate_curriculum.py
```

For the full SDK run, install the delivered pins using `uv sync --locked --extra mcp` and run the suite through that environment. MCP remains constrained to `<2`; the validated SDK is 1.30.0. The local source correction results, including the exact executed commands and skip counts, are in [VALIDATION.md](VALIDATION.md). Lint can be run after installing the `dev` extra.

In a Git checkout, `test_no_tracked_generated_files` reads that root's actual `git ls-files -z`, including deleted-but-still-tracked entries. It is expected to fail on the untouched index until Build records all 26 deletions. In a source archive it reads the embedded inventory instead. It fails if neither exists; it never falls back to the parent directory. Passing archive checks is not a claim that Build's current index is clean.

The packager can be run with `python scripts/package_release.py --output-dir DELIVERY_DIRECTORY`; that output is transport material, not source for commit. The default `dist/` output is ignored. Source validation CI includes the Git inventory guard through the existing Python discovery command.

## Scope retained from the original handoff

No CAD logic, notebooks, demo rendering, network client behavior or deployment was changed. Node/browser/Jupyter/native checks are not re-claimed as newly executed. Windows FreeCAD, physical fit and public deployment remain the existing DevOps gates detailed in [DEVOPS_HANDOFF.md](DEVOPS_HANDOFF.md).
