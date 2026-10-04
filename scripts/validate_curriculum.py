"""Validate distributable notebook and zero-build demo contracts without executing CAD."""
from __future__ import annotations

import ast
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PHASE_DIRS = (
    '01_Phase1_Sketcher_and_PartDesign',
    '02_Phase2_Constructive_Solid_Geometry',
    '03_Phase3_Python_API_and_Spreadsheets',
    'Projects/CAPSTONE_Plato_Shadows_Hardware_Mounts',
)


def validate_notebook(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        notebook = json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, OSError) as exc:
        return [f'{path}: unreadable notebook: {type(exc).__name__}']
    cells = notebook.get('cells', [])
    if notebook.get('nbformat') != 4:
        errors.append(f'{path}: notebook must use format 4')
    if not cells or cells[0].get('cell_type') != 'markdown' or '[CAPSTONE INTEGRATION TARGET]' not in ''.join(cells[0].get('source', [])):
        errors.append(f'{path}: first markdown cell needs [CAPSTONE INTEGRATION TARGET]')
    for index, cell in enumerate(cells):
        if cell.get('cell_type') != 'code':
            continue
        if cell.get('outputs') or cell.get('execution_count') is not None:
            errors.append(f'{path}: cell {index} contains saved output or execution count')
        try:
            ast.parse(''.join(cell.get('source', [])), feature_version=(3, 12))
        except SyntaxError:
            errors.append(f'{path}: cell {index} has Python syntax error')
    return errors


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.external: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == 'a' and values.get('href'):
            self.links.append(str(values['href']))
        asset = values.get('src') if tag in ('script', 'img', 'iframe') else values.get('href') if tag == 'link' else None
        if asset and (urlsplit(asset).scheme in ('http', 'https') or asset.startswith('//')):
            self.external.append(asset)


def validate_html(path: Path, docs: Path) -> list[str]:
    parser = PageParser()
    parser.feed(path.read_text(encoding='utf-8'))
    errors = [f'{path}: external runtime asset {asset}' for asset in parser.external]
    for href in parser.links:
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        target = (path.parent / unquote(parsed.path)).resolve()
        if not target.is_relative_to(docs.resolve()):
            errors.append(f'{path}: link leaves Pages root: {href}')
        elif not target.exists():
            errors.append(f'{path}: missing local link {href}')
    return errors


def main() -> int:
    errors: list[str] = []
    notebooks: list[Path] = []
    for phase in PHASE_DIRS:
        found = sorted((ROOT / phase).glob('*.ipynb'))
        if not found:
            errors.append(f'{phase}: missing lesson notebook')
        notebooks.extend(found)
    for notebook in notebooks:
        errors.extend(validate_notebook(notebook))
    pages = [ROOT / 'docs' / name for name in ('index.html', 'phase-1/index.html', 'phase-2/index.html', 'phase-3/index.html', 'capstone/index.html')]
    for page in pages:
        if not page.is_file():
            errors.append(f'{page}: missing demo')
        else:
            errors.extend(validate_html(page, ROOT / 'docs'))
    for error in errors:
        print(error)
    print(f'Curriculum validation: {len(notebooks)} notebooks, {len(pages)} pages, {len(errors)} errors')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
