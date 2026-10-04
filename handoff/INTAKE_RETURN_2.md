# FreeCAD-CV correction receipt — intake return 2

Date: 2026-10-04. Baseline repository revision (read only): `be264a594c859bc845f47001ca13caaaa24d12dc`.
Scope confirmed by Build: FreeCAD-CV only. The other six curricula are handled in their own tasks. The full intake report is supporting evidence; the CV return governs.

| Return | Correction | Evidence |
| --- | --- | --- |
| CV-1 | Root ignore rules, 26 generated-file deletions and explicit tracked-path inventory; release guard rejects these patterns | [Removal list](TRACKED_PATHS_TO_REMOVE.txt), [validation](VALIDATION.md) |
| CV-3 | Dossier, backlog, validation, interfaces, TDD records and task registry are under repository-local `handoff/`; consumers and links updated | [Build handoff](BUILD_HANDOFF.md), [backlog](BACKLOG.md) |
| CV-4 | Replace the private-network examples with documentation-only TEST-NET-1 addresses and replacement instructions | [DevOps dossier](DEVOPS_HANDOFF.md) |
| CV-8 | Root MIT license supplied; dedicated current validation document distinguishes fresh results from historical claims | [LICENSE](../LICENSE), [validation](VALIDATION.md) |

No tracked package metadata was found in this repository. The root lockfile and blank environment example are included so the existing setup instructions no longer depend on outer files. The runtime version is unchanged because this return corrects packaging and documentation.

The 12 original document/registry paths under `engineering/` are moved to `handoff/`. Build receives ordinary file additions, modifications and deletions; the correction does not change its index or rewrite history. Working-tree hygiene and the delivered archive are checked separately. The Git inventory guard remains red until Build records the 26 generated-file deletions.

Questions return through Build. Windows CAD/hardware, public deployment and sustained performance acceptance remain assigned to their existing owners.
