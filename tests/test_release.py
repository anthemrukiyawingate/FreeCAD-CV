"""Intake return 2: contracts for the repository and the delivered source tree."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts.release_guard import forbidden_paths, local_link_errors, release_inventory
from scripts.package_release import build_archive

ROOT = Path(__file__).resolve().parents[1]


class ReleaseContractTests(unittest.TestCase):
    def test_no_tracked_generated_files(self) -> None:
        paths = release_inventory(ROOT)
        self.assertEqual(forbidden_paths(paths), [], 'Build must remove tracked generated paths listed in handoff/TRACKED_PATHS_TO_REMOVE.txt')

    def test_release_files_are_inside_repository(self) -> None:
        for relative in ('.gitignore', 'LICENSE', 'uv.lock', 'docs/.nojekyll',
                         'handoff/DEVOPS_HANDOFF.md', 'handoff/BACKLOG.md',
                         'handoff/VALIDATION.md', 'handoff/tasks.json'):
            with self.subTest(path=relative):
                path = ROOT / relative
                self.assertTrue(path.is_file(), relative)
                self.assertTrue(path.resolve().is_relative_to(ROOT))
        self.assertIn('MIT License', (ROOT / 'LICENSE').read_text())

    def test_ignore_covers_all_generated_categories(self) -> None:
        rules = set((ROOT / '.gitignore').read_text().splitlines())
        for rule in ('__pycache__/', '*.py[cod]', '.venv/', 'venv/', '.pytest_cache/',
                     '.mypy_cache/', '.ruff_cache/', '.ipynb_checkpoints/',
                     'build/', 'dist/', 'out/', '*.egg-info/', 'node_modules/'):
            self.assertIn(rule, rules)

    def test_document_links_resolve_inside_repository(self) -> None:
        paths = release_inventory(ROOT)
        errors = [error for relative in paths if relative.endswith('.md')
                  and (ROOT / relative).is_file()
                  for error in local_link_errors(ROOT / relative, ROOT)]
        self.assertEqual(errors, [])

    def test_docs_and_tests_do_not_use_private_example_addresses(self) -> None:
        import re
        prefix = '.'.join(('192', '168'))
        pattern = re.compile(r'\b' + re.escape(prefix) + r'\.\d{1,3}\.\d{1,3}\b')
        for path in [ROOT / 'README.md', *sorted((ROOT / 'handoff').glob('*.md')),
                     *sorted((ROOT / 'tests').glob('*.py'))]:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(pattern.search(path.read_text()))

    def test_pattern_guard_rejects_nested_generated_paths(self) -> None:
        bad = ['module/__pycache__/file.pyc', 'module/file.pyo', 'module/file.pyd',
               'build/lib/file.py', 'sub/dist/app.zip', 'out/electron/app',
               '.venv/lib/file.py', 'venv/lib/file.py', 'nested/app.egg-info/PKG-INFO',
               'sub/.pytest_cache/state', '.mypy_cache/state', '.ruff_cache/state',
               'notebooks/.ipynb_checkpoints/draft.ipynb', 'node_modules/pkg/index.js']
        self.assertEqual(forbidden_paths(bad), sorted(bad))
        self.assertEqual(forbidden_paths(['cortexcad/client.py', 'docs/index.html',
                                         'handoff/BUILD_HANDOFF.md']), [])

    def test_git_inventory_includes_deleted_but_still_tracked_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / '.git').mkdir()
            result = type('Result', (), {'stdout': b'module/__pycache__/gone.pyc\0README.md\0'})()
            with patch('scripts.release_guard.subprocess.run', return_value=result) as run:
                paths = release_inventory(root)
            self.assertIn('module/__pycache__/gone.pyc', forbidden_paths(paths))
            self.assertIn('ls-files', run.call_args.args[0])
            self.assertIn('-z', run.call_args.args[0])
            self.assertNotIn('--deleted', run.call_args.args[0])

    def test_archive_inventory_cannot_escape_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'SHA256SUMS.json').write_text(json.dumps({'../outside.md': '0' * 64}))
            with self.assertRaises(ValueError):
                release_inventory(root)

    def test_missing_inventory_is_not_a_silent_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                release_inventory(Path(temporary))

    def test_local_link_guard_rejects_escape_even_if_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = parent / 'source'
            root.mkdir()
            (parent / 'outside.md').write_text('not part of delivery')
            readme = root / 'README.md'
            readme.write_text('[outside](../outside.md)\n[missing](handoff/missing.md)')
            errors = local_link_errors(readme, root)
            self.assertEqual(len(errors), 2)
            self.assertTrue(any('outside' in error for error in errors))

    def test_archive_contains_v2_root_and_handoff_without_generated_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive = build_archive(ROOT, Path(temporary))
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
                self.assertTrue(all(name.startswith('FreeCAD-CV/') for name in names))
                inventory = json.loads(bundle.read('FreeCAD-CV/SHA256SUMS.json'))
                self.assertEqual(forbidden_paths(list(inventory)), [])
                for relative in ('LICENSE', '.gitignore', 'uv.lock', 'handoff/VALIDATION.md',
                                 'handoff/DEVOPS_HANDOFF.md', 'handoff/BACKLOG.md',
                                 'handoff/TRACKED_PATHS_TO_REMOVE.txt', '.github/workflows/ci.yml'):
                    self.assertIn(relative, inventory)
                for relative, digest in inventory.items():
                    self.assertEqual(hashlib.sha256(bundle.read('FreeCAD-CV/' + relative)).hexdigest(), digest)
                self.assertFalse(any(name.startswith('FreeCAD-CV/engineering/') for name in names))


if __name__ == '__main__':
    unittest.main()
