"""Release guard contracts are defined before their implementation."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from scripts.validate_curriculum import validate_notebook, validate_html
from scripts.package_release import source_files

class DeliveryContractTests(unittest.TestCase):
    def test_notebook_requires_capstone_first_and_clean_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'lesson.ipynb'
            path.write_text(json.dumps({'nbformat':4, 'cells':[
                {'cell_type':'markdown','source':['No capstone target']},
                {'cell_type':'code','source':['print(1)'],'execution_count':1,'outputs':[{'text':['secret']}]}]}))
            errors = validate_notebook(path)
            self.assertTrue(any('CAPSTONE' in error for error in errors))
            self.assertTrue(any('output' in error for error in errors))

    def test_code_cells_must_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'lesson.ipynb'
            path.write_text(json.dumps({'nbformat':4, 'cells':[
                {'cell_type':'markdown','source':['[CAPSTONE INTEGRATION TARGET] fixture']},
                {'cell_type':'code','source':['def broken('],'execution_count':None,'outputs':[]}]}))
            self.assertTrue(any('syntax' in error for error in validate_notebook(path)))

    def test_demo_cannot_depend_on_remote_runtime_or_missing_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'index.html'
            path.write_text('<html><script src="https://example.com/runtime.js"></script><a href="missing/index.html">Missing</a></html>')
            errors = validate_html(path, Path(tmp))
            self.assertTrue(any('external' in error for error in errors))
            self.assertTrue(any('missing' in error for error in errors))

    def test_release_excludes_environment_caches_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'README.md').write_text('course')
            (root/'cortexcad').mkdir()
            (root/'cortexcad'/'client.py').write_text('pass')
            (root/'cortexcad'/'.env').write_text('TOKEN=private')
            (root/'cortexcad'/'leak.py').symlink_to('/etc/passwd')
            (root/'.venv').mkdir()
            (root/'.venv'/'private.py').write_text('token')
            files = {str(p.relative_to(root)) for p in source_files(root)}
            self.assertEqual(files, {'README.md','cortexcad/client.py'})

if __name__ == '__main__':
    unittest.main()
