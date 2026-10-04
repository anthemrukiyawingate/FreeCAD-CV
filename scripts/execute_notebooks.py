"""Execute every lesson in a temporary offline kernel without modifying source files."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        import nbformat
        from nbclient import NotebookClient
    except ImportError:
        print("Install notebook dependencies: python -m pip install -e '.[notebooks]'", file=sys.stderr)
        return 2
    paths = sorted(path for folder in (
        '01_Phase1_Sketcher_and_PartDesign', '02_Phase2_Constructive_Solid_Geometry',
        '03_Phase3_Python_API_and_Spreadsheets', 'Projects/CAPSTONE_Plato_Shadows_Hardware_Mounts',
    ) for path in (ROOT / folder).glob('*.ipynb'))
    if len(paths) != 4:
        print(f'Expected 4 notebooks; found {len(paths)}', file=sys.stderr)
        return 1
    with TemporaryDirectory(prefix='cortexcad-kernel-') as temporary:
        scratch = Path(temporary)
        kernel = scratch / 'kernels/cortexcad-validation'
        kernel.mkdir(parents=True)
        (kernel / 'kernel.json').write_text(json.dumps({
            'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
            'display_name': 'CortexCAD offline validation', 'language': 'python',
            'env': {'CORTEXCAD_LIVE': '0'},
        }), encoding='utf-8')
        overrides = {'CORTEXCAD_LIVE':'0', 'JUPYTER_PATH':str(scratch),
                     'IPYTHONDIR':str(scratch / 'ipython'), 'JUPYTER_RUNTIME_DIR':str(scratch / 'runtime')}
        previous = {key:os.environ.get(key) for key in overrides}
        os.environ.update(overrides)
        try:
            for path in paths:
                notebook = nbformat.read(path, as_version=4)
                nbformat.validate(notebook)
                NotebookClient(notebook, timeout=60, kernel_name='cortexcad-validation',
                               resources={'metadata':{'path':str(path.parent)}}).execute()
                print(f'PASS offline execution: {path.relative_to(ROOT)}')
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    print('Four offline lessons executed; no CAD endpoint was called; source notebooks remain clean.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
