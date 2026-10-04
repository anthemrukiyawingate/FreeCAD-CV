"""Read-only release hygiene checks for a Git checkout or a source archive."""
from __future__ import annotations

from fnmatch import fnmatchcase
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import unquote, urlsplit

# Keep these categories aligned with the repository-root .gitignore.
GENERATED_DIRECTORIES = frozenset({
    '__pycache__', '.cache', '.pytest_cache', '.mypy_cache', '.ruff_cache',
    '.hypothesis', '.ipynb_checkpoints', '.tox', '.nox', '.venv', 'venv',
    'env', 'ENV', 'build', 'dist', 'out', 'htmlcov', 'coverage', 'artifacts',
    'node_modules',
})
GENERATED_FILES = ('*.py[cod]', '*.egg-info', '.coverage', '.coverage.*',
                   'coverage.xml', '*.tsbuildinfo')


def forbidden_paths(paths: list[str]) -> list[str]:
    """Return generated paths, including nested metadata and deleted index entries."""
    return sorted(path for path in paths if any(
        part in GENERATED_DIRECTORIES or any(fnmatchcase(part, pattern) for pattern in GENERATED_FILES)
        for part in PurePosixPath(path).parts
    ))


def _contained_paths(paths: list[str], root: Path) -> list[str]:
    for name in paths:
        relative = PurePosixPath(name)
        if (not name or relative.is_absolute() or '..' in relative.parts
                or '\\' in name or ':' in name
                or not (root / name).resolve().is_relative_to(root.resolve())):
            raise ValueError('Release inventory contains a path outside the repository')
    return sorted(paths)


def release_inventory(root: Path) -> list[str]:
    """Read this root's Git index, or the inventory embedded in its source archive.

    Never walks upward looking for Git and never filters out deleted tracked
    paths. In an archive there is no Git index: the manifest is the inventory.
    """
    if (root / '.git').exists():
        result = subprocess.run(
            ['git', '-C', str(root), 'ls-files', '-z'],
            check=True, capture_output=True, timeout=10,
        )
        paths = result.stdout.decode('utf-8').split('\0')
        return _contained_paths([path for path in paths if path], root)
    manifest = root / 'SHA256SUMS.json'
    if not manifest.is_file():
        raise ValueError('Release root requires its own .git inventory or SHA256SUMS.json')
    inventory = json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(inventory, dict) or not all(isinstance(key, str) for key in inventory):
        raise ValueError('Release inventory must be a path-to-checksum object')
    return _contained_paths(list(inventory), root)


def local_link_errors(document: Path, root: Path) -> list[str]:
    """Require local inline/reference Markdown and HTML links to stay in the tree."""
    text = document.read_text(encoding='utf-8')
    inline = re.findall(r'!?\[[^\]]*\]\(\s*(<[^>]*>|[^\s)]+)(?:\s+[^)]*)?\)', text)
    reference = re.findall(r'^\s*\[[^\]]+\]:\s*(<[^>]*>|\S+)', text, flags=re.MULTILINE)
    html = re.findall(r'(?:href|src)=["\']([^"\']+)["\']', text)
    errors: list[str] = []
    for target in (*inline, *reference, *html):
        parsed = urlsplit(target.strip('<>'))
        if parsed.scheme in ('http', 'https', 'mailto') or parsed.netloc or not parsed.path:
            continue
        candidate = (document.parent / unquote(parsed.path)).resolve()
        label = document.relative_to(root).as_posix()
        if parsed.scheme or not candidate.is_relative_to(root.resolve()):
            errors.append(f'{label}: local link outside repository: {target}')
        elif not candidate.exists():
            errors.append(f'{label}: missing local link: {target}')
    return errors
