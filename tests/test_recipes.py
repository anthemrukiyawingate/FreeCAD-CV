"""Contract tests: native geometry assertions still require a real FreeCAD run."""

import ast
import json
import contextlib
import io
import math
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

from cortexcad.recipes import DEFAULTS, PHASES, build_script, validate_parameters


class ParameterContractTests(unittest.TestCase):
    def test_every_phase_has_a_complete_independent_default(self) -> None:
        for phase in PHASES:
            validated = validate_parameters(phase)
            self.assertEqual(validated, DEFAULTS[phase])
            validated[next(iter(validated))] = 999
            self.assertNotEqual(validated, DEFAULTS[phase])

    def test_bad_phase_is_rejected(self) -> None:
        for phase in ("", "Sketcher", "__import__('os')", None, []):
            with self.subTest(phase=phase), self.assertRaises(ValueError):
                build_script(phase)  # type: ignore[arg-type]

    def test_non_object_parameters_are_rejected(self) -> None:
        for parameters in ([], "{}", 10):
            with self.subTest(parameters=parameters), self.assertRaises(ValueError):
                build_script("sketcher", parameters)  # type: ignore[arg-type]

    def test_unknown_keys_cannot_become_executable_text(self) -> None:
        with self.assertRaises(ValueError):
            build_script("sketcher", {"length; import os": 20})

    def test_non_numeric_nonfinite_and_excessive_dimensions_fail_before_ipc(self) -> None:
        bad_values = [True, False, None, "40", "__import__('os')", 0, -1,
                      math.nan, math.inf, -math.inf, 2001, 10 ** 1000]
        for phase in PHASES:
            key = next(iter(DEFAULTS[phase]))
            for value in bad_values:
                with self.subTest(phase=phase, value=repr(value)[:50]), self.assertRaises(ValueError):
                    build_script(phase, {key: value})

    def test_csg_intersection_must_be_partial_and_nonzero(self) -> None:
        for overlap in (0, 40, 50):
            with self.subTest(overlap=overlap), self.assertRaises(ValueError):
                build_script("csg", {"length": 40, "overlap": overlap})

    def test_mount_holes_retain_edge_material_and_clear_upright(self) -> None:
        for change in ({"mount_pitch_x": 150}, {"mount_pitch_y": 90},
                       {"bracket_height": 20}, {"edge_margin": 1}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                build_script("capstone", change)

    def test_mount_holes_cannot_overlap_one_another(self) -> None:
        for axis in ("mount_pitch_x", "mount_pitch_y"):
            with self.subTest(axis=axis), self.assertRaises(ValueError):
                build_script("capstone", {axis: 5.0, "fastener_diameter": 5.5})

    def test_housing_apertures_retain_wall_material(self) -> None:
        for change in ({"cable_diameter": 30}, {"lens_diameter": 40},
                       {"sensor_length": 5}, {"clearance": 11}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                build_script("capstone", change)

    def test_measurement_example_is_strict_complete_schema(self) -> None:
        root = Path(__file__).resolve().parents[1]
        path = root / "Projects/CAPSTONE_Plato_Shadows_Hardware_Mounts/measurement.example.json"
        fixture = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(set(fixture), set(DEFAULTS["capstone"]))
        self.assertEqual(validate_parameters("capstone", fixture), DEFAULTS["capstone"])


class GeneratedScriptTests(unittest.TestCase):
    def test_scripts_compile_for_native_python_311(self) -> None:
        for phase in PHASES:
            ast.parse(build_script(phase), feature_version=(3, 11))

    def test_deterministic_output_and_parameter_data_round_trip(self) -> None:
        for phase in PHASES:
            source = build_script(phase)
            self.assertEqual(source, build_script(phase, dict(reversed(list(DEFAULTS[phase].items())))))
            tree = ast.parse(source)
            node = next(n for n in tree.body if isinstance(n, ast.AnnAssign)
                        and isinstance(n.target, ast.Name) and n.target.id == "p")
            payload = ast.literal_eval(node.value.args[0])  # type: ignore[union-attr]
            self.assertEqual(json.loads(payload), DEFAULTS[phase])

    def test_existing_document_is_rejected_without_mutation(self) -> None:
        for phase in PHASES:
            source = build_script(phase)
            tree = ast.parse(source)
            name_node = next(n for n in tree.body if isinstance(n, ast.AnnAssign)
                             and isinstance(n.target, ast.Name) and n.target.id == "document_name")
            name = ast.literal_eval(name_node.value)
            freecad = ModuleType("FreeCAD")
            freecad.listDocuments = lambda: {name: object()}  # type: ignore[attr-defined]
            events: list[str] = []
            freecad.newDocument = lambda _: events.append("mutation")  # type: ignore[attr-defined]
            imports = {"FreeCAD": freecad, "Part": ModuleType("Part"), "Sketcher": ModuleType("Sketcher")}
            with patch.dict(sys.modules, imports), self.assertRaisesRegex(RuntimeError, "already exists"):
                exec(compile(source, f"{phase}.py", "exec"), {})
            self.assertEqual(events, [])

    def test_transaction_failure_aborts_and_recomputes(self) -> None:
        for phase in PHASES:
            events: list[str] = []

            class FailedDocument:
                Name = "test_document"
                def openTransaction(self, label: str) -> None:
                    events.append("open")
                def addObject(self, *args: object) -> None:
                    raise RuntimeError("controlled failure")
                def abortTransaction(self) -> None:
                    events.append("abort")
                def recompute(self) -> None:
                    events.append("recompute")

            document = FailedDocument()
            freecad = ModuleType("FreeCAD")
            freecad.listDocuments = lambda: {}  # type: ignore[attr-defined]
            freecad.newDocument = lambda _: document  # type: ignore[attr-defined]
            freecad.setActiveDocument = lambda _: None  # type: ignore[attr-defined]
            freecad.ActiveDocument = document  # type: ignore[attr-defined]
            imports = {"FreeCAD": freecad, "Part": ModuleType("Part"), "Sketcher": ModuleType("Sketcher")}
            with patch.dict(sys.modules, imports), self.assertRaisesRegex(RuntimeError, "controlled failure"):
                exec(compile(build_script(phase), f"{phase}.py", "exec"), {})
            self.assertEqual(events, ["open", "abort", "recompute"])

    def test_native_assertions_are_explicit_in_all_phases(self) -> None:
        for phase in PHASES:
            source = build_script(phase)
            self.assertIn("App.ActiveDocument.recompute()", source)
            self.assertIn(".isValid()", source)
            self.assertIn(".Solids", source)
            self.assertIn("math.isclose(", source)
            self.assertNotIn("App.closeDocument", source)
        self.assertIn("sketch.FullyConstrained", build_script("sketcher"))
        self.assertIn("Spreadsheet::Sheet", build_script("parametric"))
        self.assertIn("setExpression", build_script("parametric"))


class NotebookContractTests(unittest.TestCase):
    def test_four_lessons_execute_offline_from_an_unrelated_directory(self) -> None:
        root = Path(__file__).resolve().parents[1]
        paths = [root / "01_Phase1_Sketcher_and_PartDesign/01_constrained_mount.ipynb",
                 root / "02_Phase2_Constructive_Solid_Geometry/02_boolean_lab.ipynb",
                 root / "03_Phase3_Python_API_and_Spreadsheets/03_json_spreadsheet.ipynb",
                 root / "Projects/CAPSTONE_Plato_Shadows_Hardware_Mounts/04_hardware_integration.ipynb"]
        from cortexcad.client import FreeCADClient
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"CORTEXCAD_LIVE": "0", "CORTEXCAD_ROOT": str(root), "CORTEXCAD_MEASUREMENTS": ""}), patch.object(FreeCADClient, "run_recipe", side_effect=AssertionError("offline notebook attempted IPC")):
            try:
                os.chdir(directory)
                for path in paths:
                    notebook = json.loads(path.read_text(encoding="utf-8"))
                    self.assertEqual(notebook["cells"][0]["cell_type"], "markdown")
                    self.assertTrue("".join(notebook["cells"][0]["source"]).startswith("[CAPSTONE INTEGRATION TARGET]"))
                    namespace: dict[str, object] = {}
                    with contextlib.redirect_stdout(io.StringIO()):
                        for cell in notebook["cells"]:
                            if cell["cell_type"] == "code":
                                self.assertEqual(cell["outputs"], [])
                                exec(compile("".join(cell["source"]), str(path), "exec"), namespace)
            finally:
                os.chdir(original)


if __name__ == "__main__":
    unittest.main()
