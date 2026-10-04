# Delivery harness TDD evidence

Date: 2026-10-03. Tests were defined before implementation.

1. `python3 -m unittest discover -s tests -p test_delivery.py -v` initially exited 1 with `ModuleNotFoundError: No module named 'scripts.validate_curriculum'`.
2. Implemented the notebook/static validators and allow-listed source archive collector.
3. The same command passed 4 tests: notebook integration callout and clean outputs, code syntax, remote dependency/missing local link rejection, and environment/symlink exclusion.
4. `python3 -m unittest discover -s tests -p test_task_harness.py -v` initially exited 1 with `ModuleNotFoundError: No module named 'scripts.task_harness'`.
5. Implemented the structured five-sprint registry and packet formatter.
6. The same command passed 3 tests: all five sprints with concrete fields, test-first/external ownership packet content, and unknown task rejection.

These tests verify source handoff rules. They do not validate GitHub permissions, a deployment, archive transport, physical hardware or FreeCAD geometry. Actual combined suite results are recorded separately in QA_REPORT.md.
