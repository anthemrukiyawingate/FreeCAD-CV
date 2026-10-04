"""Create an in-repository source handoff and checksum; never changes Git or deploys."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_DIRS = {'cortexcad', 'scripts', 'tests', 'docs', 'handoff', 'Projects',
                '01_Phase1_Sketcher_and_PartDesign', '02_Phase2_Constructive_Solid_Geometry',
                '03_Phase3_Python_API_and_Spreadsheets', '.github'}
ALLOWED_FILES = {'README.md', 'LICENSE', 'pyproject.toml', 'uv.lock', '.gitignore',
                 '.gitattributes', '.env.example'}
EXCLUDED = {'__pycache__', '.ipynb_checkpoints', '.ruff_cache', '.pytest_cache',
            '.mypy_cache', '.cache', '.venv', 'venv', 'env', 'ENV', 'artifacts',
            'dist', 'build', 'out', 'node_modules', 'htmlcov', 'coverage', '.tox', '.nox'}
SUFFIXES = {'.py', '.md', '.html', '.json', '.ipynb', '.toml', '.yml', '.yaml', '.cjs', '.txt', '.ps1', '.sh'}
ARCHIVE_NAME = 'FreeCAD-CV-intake-return-2.zip'


def source_files(root: Path) -> list[Path]:
    """Walk only source directories; generated output never enters the archive."""
    selected: list[Path] = []
    for directory, folders, names in os.walk(root, followlinks=False):
        parent = Path(directory)
        folders[:] = [name for name in folders
                      if name not in EXCLUDED and not name.endswith('.egg-info')
                      and not (parent / name).is_symlink()
                      and (name in ALLOWED_DIRS if parent == root else not name.startswith('.'))]
        for name in names:
            path = parent / name
            if path.is_symlink() or not path.is_file():
                continue
            if parent == root:
                if name in ALLOWED_FILES:
                    selected.append(path)
            elif name == '.nojekyll' or (not name.startswith('.') and path.suffix in SUFFIXES):
                selected.append(path)
    return sorted(selected)


def build_archive(root: Path, output: Path) -> Path:
    """Package one self-contained FreeCAD-CV root and its exact source inventory."""
    files = source_files(root)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in files}
    archive = output / ARCHIVE_NAME
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            bundle.write(path, 'FreeCAD-CV/' + path.relative_to(root).as_posix())
        bundle.writestr('FreeCAD-CV/SHA256SUMS.json', json.dumps(manifest, indent=2) + '\n')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / (archive.name + '.sha256')).write_text(f'{digest}  {archive.name}\n', encoding='utf-8')
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    archive = build_archive(ROOT, args.output_dir)
    print(json.dumps({'archive': str(archive), 'source_files': len(source_files(ROOT)),
                      'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
